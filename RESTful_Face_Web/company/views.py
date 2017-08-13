from django.shortcuts import render
# request and response
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
# view
from rest_framework import viewsets, mixins
# parser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser, FileUploadParser
# serializers
from .serializers import CompanySerializer, PersonSerializer, FaceSerializer, CommandSerializer, AppSerializer
# models
from django.contrib.auth.models import User
from . import models
from .models import Person, Face, Command, App
# permissions
from rest_framework import permissions
from .permissions import CompanyPermission, CompaniesPermission
# logging
import logging
log = logging.getLogger(__name__)
# utils
from .utils.random_unique_id import generate_unique_id
from .utils.retrieve_admin import get_admin
from RESTful_Face_Web.settings import myDBManager
from rest_framework.decorators import list_route
# service
from service import services
# image
from PIL import Image
from io import BytesIO

class CompaniesViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    """
    Permission:
    1) An admin user can list and create companies;
    2) An anonymous user can create companies.
    """
    queryset = User.objects.using('default').all()
    serializer_class = CompanySerializer
    permission_classes = (CompaniesPermission, )

    # override to create dynamic database
    def perform_create(self, serializer):
        serializer.save(first_name=generate_unique_id(get_admin()))
        log.info("Company '%s' created !" % (serializer.data['username']))

# due to special permission requirement, splite list/create with CRUD on single object
class CompanyViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    Permission:
    1) An admin user can retrieve and delete a company;
    2) An anonymous user can retrieve and update a company.
    """
    queryset = User.objects.using('default').all()
    serializer_class = CompanySerializer
    permission_classes = (CompanyPermission, )

    # copy and modify UpdateModelMixin to do partial modification
    def update(self, request, *args, **kwargs):
        company = self.get_object()
        serializer = self.get_serializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        log.info("Company '%s' updated!" % (serializer.data['username']))
        return Response(serializer.data)

    # override to do CASCADE delete and drop the database
    def perform_destroy(self, instance):
        apps = App.objects.filter(company=instance)
        for app in apps:
            persons = Person.objects.using(app.appID)
            [person.delete() for person in persons]  # this will delete the image file

            myDBManager.drop_database(app.appID)   #  this will delete the database file
            # app, commands will be deleted automatically
        instance.delete()

class AppViewSet(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    """
    Permissions:
    1) An admin user can list and retrieve all apps;
    2) An company user can list, retrieve, create, update and delete his own apps.
    """
    serializer_class = AppSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return App.objects.filter(company=self.request.user)

    def perform_create(self, serializer):
        app = serializer.save(company=self.request.user, appID=generate_unique_id(get_admin()))

        myDBManager.create_database(app.appID)
        myDBManager.create_table(app.appID, Person, 'person')
        myDBManager.create_table(app.appID, Face, 'face')
        log.info("Database for app %s of company %s (%s) Created!" % (app.app_name, app.company.username, app.company.first_name))

    def perform_destroy(self, app):
        # delete the database and mark it as inactive, but keep the instance
        persons = Person.objects.using(app.appID)
        [person.delete() for person in persons]

        myDBManager.drop_database(app.appID)
        app.is_active = False
        app.save()


class PersonViewSet(viewsets.ModelViewSet):
    """
    Permissions:
    Only company it self can list, retrieve, create, update and delete persons.
    """
    serializer_class = PersonSerializer
    permission_classes = (permissions.IsAuthenticated, )

    # override to using specific database
    def get_queryset(self):
        app = models.get_target_app(self.request.user, appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app==None:
            raise ValidationError({'Person': 'App Not Found!'})
        return Person.objects.using(app.appID).all()

    # override to pass generated random ID
    def perform_create(self, serializer):
        app = models.get_target_app(self.request.user, appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app == None:
            raise ValidationError({'Create Person': 'App Not Found!'})
        serializer.save(userID=generate_unique_id(self.request.user), appID=app.appID)

    # override to do partial update
    def update(self, request, *args, **kwargs):
        person = self.get_object()
        serializer = self.get_serializer(person, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class FaceViewSet(viewsets.ModelViewSet):
    """
    Permissions:
    Only company it self can list, retrieve, create, delete and update faces.
    """
    serializer_class = FaceSerializer
    permission_classes = (permissions.IsAuthenticated, )
    parser_classes = (MultiPartParser, FormParser, JSONParser, FileUploadParser)

    def get_queryset(self):
        # get the person
        app = models.get_target_app(self.request.user, appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app==None:
            raise ValidationError({'Person': 'App not found!'})
        person = self.__get_person(app, self.request.data)

        # get person's all faces
        return Face.objects.using(app.appID).filter(person__in=person)

    def perform_create(self, serializer):
        print("creating")
        app = models.get_target_app(self.request.user,
                                    appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        print(app.app_name)
        if app==None:
            raise ValidationError({'Create Face', 'App Not Found!'})
        person = self.__get_person(app, self.request.data)
        if len(person) != 1:
            log.error('No person specified!')
            raise ValidationError({'FaceViewSet': 'Unique person name or id need to be given!'})

        print(person[0].name)
        serializer.save(person=person[0], image=None if 'image' not in self.request.data else self.request.data['image'])

    def perform_update(self, serializer):
        serializer.save(image=None if 'image' not in self.request.data else self.request.data['image'])

    # filter to get company's faces
    def __get_person(self, app, data):
        person = Person.objects.using(app.appID)
        if 'name' in data:
            person = person.filter(name=data['name'])
        elif 'userID' in self.request.data:
            person = person.filter(userID=data['userID'])

        return [p for p in person]


def log_command(service_config):
    service = service_config[2]()
    def decorator(func):
        def func_wrapper(self, request):
            # generate the command
            ret = Command.objects.create(company=request.user.first_name, serviceID=service_config[0])
            ret.save()
            log.info("Service [%s] history has been stored!" %(service_config[1]))
            return func(self, request, service)
        return func_wrapper
    return decorator

class CommandViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """
    Permissions:
    Both admin and owner can only list and retrieve commands.
    """
    serializer_class = CommandSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        if self.request.user.is_superuser:
            commands = Command.objects.all()
            if 'company' in self.request.data:
                commands = commands.filter(company=self.request.data['company'])
            return commands
        else:
            print(self.request.user)
            return Command.objects.filter(company=self.request.user.first_name)

    # https://www.thecodeship.com/patterns/guide-to-python-function-decorators/
    @list_route(methods=['post', 'put'])
    @log_command(services.QUALITY_CHECK)
    def quality_check(self, request, service):
        results = service.execute()
        log.info('Service: '+services.QUALITY_CHECK[1])
        return Response(results)
'''
    @list_route(methods=['post', 'put'])
    @log_command(services.LANDMARK_DETECTION)
    def landmark_detection(self, request, service):
        results = service.execute()
        return Response(results)

    @list_route(methods=['post', 'put'])
    @log_command(services.ATTRIBUTE_PREDICATE)
    def attribute_predication(self, request, service):
        results = service.execute()
        return Response(results)

    @list_route(methods=['post', 'put'])
    @log_command(services.RECOGNITION)
    def recognition(self, request, service):
        results = service.execute()
        return Response(results)

    @list_route(methods=['post', 'put'])
    @log_command(services.FEATURE_EXTRACTION)
    def feature_extraction(self, request, service):
        results = service.execute()
        return Response(results)

    @list_route(methods=['post', 'put'])
    @log_command(services.ENHANCEMENT)
    def enhancement(self, request, service):
        results = service.execute()
        return Response(results)
'''