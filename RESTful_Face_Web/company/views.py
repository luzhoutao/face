# request and response
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
# view
from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route
# parser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser, FileUploadParser
# serializers
from .serializers import CompanySerializer, SubjectSerializer, FaceSerializer, CommandSerializer, AppSerializer, Token2TokenSerializer
# models
from django.contrib.auth.models import User
from . import models
from .models import Subject, Face, Command, App, Feature, ClassifierModel, Token2Token, FeatureTemplate
from expiring_token.models import ExpiringToken
# permissions
from rest_framework import permissions
from .permissions import CompanyPermission, CompaniesPermission, IsSuperuser, TokenPermission
# logging
import logging
log = logging.getLogger(__name__)
# utils
from .utils.random_unique_id import generate_unique_id
from .utils.retrieve_admin import get_admin
from RESTful_Face_Web.settings import EXPIRING_TOKEN_LIFESPAN, MEDIA_ROOT
from rest_framework.decorators import list_route
import datetime
from PIL import Image
import numpy as np
from django.utils import timezone
import os, shutil
import cv2
import json
# service
from service import services, extraction

#import uwsgi
from RESTful_Face_Web.runtime_db import load_database
from RESTful_Face_Web.runtime_db.runtime_database import MySQLManager
myDBManager = MySQLManager()
#from RESTful_Face_Web.runtime_db.runtime_database import SQLiteManager
#myDBManager = SQLiteManager()

# error code in response
NO_APP_ERROR = 5501
INVALID_REQUEST_ERROR = 5502
IMAGE_FORMAT_ERROR = 5503
NO_IMAGE_ERROR = 5504
NO_SUBJECT_ERROR = 5505

   
class CompaniesViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = User.objects.using('default').all()
    serializer_class = CompanySerializer
    permission_classes = (CompaniesPermission, )
    #authentication_classes = (ExpiringTokenAuthentication, )

    # override to create dynamic database
    def perform_create(self, serializer):
        serializer.save(first_name=generate_unique_id(get_admin()))
        log.info("Company '%s' created !" % (serializer.data['username']))


    @list_route(methods=['get'], permission_classes=[permissions.IsAdminUser, ])
    def token2token(self, request):
        if 'companyID' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'info': 'companyID is required.'})

        company = User.objects.filter(first_name=request.data['companyID'])
        if len(company) != 1:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'info': 'Please provide valid and unique companyID.'})
        company = company[0]
        try:
            lifespan = datetime.timedelta(seconds=0)
            if 'days' in request.data:
                lifespan = lifespan + datetime.timedelta(int(request.data['days']))
            if 'seconds' in request.data:
                lifespan = lifespan + datetime.timedelta(int(request.data['seconds']))
            # default lifespan is set in settings.py
            if lifespan.total_seconds() == 0:
                lifespan = EXPIRING_TOKEN_LIFESPAN

            token2token = Token2Token.objects.filter(company=company)
            if len(token2token) == 0:
                token2token = Token2Token.objects.create(company=company, duration=lifespan)
            else:
                token2token[0].duration = token2token[0].duration + lifespan
                token2token[0].save()
                token2token = token2token[0]

            serializer = Token2TokenSerializer(token2token)
            return Response(serializer.data)
        except:
            # days, seconds parse error
            return Response(status=status.HTTP_400_BAD_REQUEST)

# due to special permission requirement, splite list/create with CRUD on single object
class CompanyViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = User.objects.using('default').all()
    serializer_class = CompanySerializer
    permission_classes = (CompanyPermission, )
    lookup_field = 'first_name'

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
        apps = App.objects.filter(company=instance, is_active=True)
        for app in apps:
            persons = Subject.objects.using(app.appID)
            [ person.delete() for person in persons ]  # this will delete the image file

            myDBManager.drop_database(app.appID)   #  this will delete the database file
            app.delete()
            # app, commands will be deleted automatically
        instance.delete()

    @detail_route(methods=['put', 'post'], permission_classes=[IsSuperuser, ])
    def authorization(self, request, pk=None):
        staff = self.get_object()
        staff.is_staff = True
        staff.save()
        return Response({'Authorization': staff.username+' has been authorized!'})

class AppViewSet(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):

    serializer_class = AppSerializer
    permission_classes = (permissions.IsAuthenticated, TokenPermission)
    lookup_field = 'appID'

    def get_queryset(self):
        return App.objects.filter(company=self.request.user)

    def perform_create(self, serializer):
        app = serializer.save(company=self.request.user, appID=generate_unique_id(get_admin()))

        myDBManager.create_database(app.appID)
        myDBManager.create_table(app.appID, Subject, 'subject')
        myDBManager.create_table(app.appID, Face, 'face')
        myDBManager.create_table(app.appID, Feature, 'feature')
        myDBManager.create_table(app.appID, ClassifierModel, 'classifier')
        myDBManager.create_table(app.appID, FeatureTemplate, 'feature template')
        log.info("Database for app %s of company %s (%s) Created!" % (app.app_name, app.company.username, app.company.first_name))
        #uwsgi.reload()

    def perform_destroy(self, app):
        # delete the database and mark it as inactive, but keep the instance
        #persons = Person.objects.using(app.appID)
        #[person.delete() for person in persons]

        face_path = os.path.join(MEDIA_ROOT, 'faces', app.appID)
        if os.path.exists(face_path):
            shutil.rmtree(face_path)

        myDBManager.drop_database(app.appID)
        app.is_active = False
        app.save()


class SubjectViewSet(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    serializer_class = SubjectSerializer
    permission_classes = (permissions.IsAuthenticated, TokenPermission)
    lookup_field = 'subjectID'

    # override to using specific database
    def get_queryset(self):
        app = models.get_target_app(self.request.user, appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app==None:
            raise ValidationError({'info': 'App Not Found!', 'error_code': NO_APP_ERROR})
        return Subject.objects.using(app.appID).all()

    # override to pass generated random ID
    def perform_create(self, serializer):
        app = models.get_target_app(self.request.user, appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app == None:
            raise ValidationError({'info': 'App Not Found!', 'error_code': NO_APP_ERROR})
        serializer.save(subjectID=generate_unique_id(self.request.user), appID=app.appID)

    # override to do partial update
    def update(self, request, *args, **kwargs):
        subject = self.get_object()
        serializer = self.get_serializer(subject, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class FaceViewSet(viewsets.ModelViewSet):
    serializer_class = FaceSerializer
    permission_classes = (permissions.IsAuthenticated, TokenPermission)
    parser_classes = (MultiPartParser, FormParser, JSONParser, FileUploadParser)
    feature_extractor = extraction.FeatureExtractor()

    def get_queryset(self):
        # get the person
        app = models.get_target_app(self.request.user, appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app==None:
            raise ValidationError({'info': 'App not found!', 'error_code': NO_APP_ERROR})
        
        subject = Subject.objects.using(app.appID)
        if 'subjectID' in self.request.data:
            subject = subject.filter(subjectID=self.request.data['subjectID'])
            if len(subject) == 0:
                raise ValidationError({'info': 'Invalid subject ID', 'error_code': NO_SUBJECT_ERROR})

        # get subject's all faces
        return Face.objects.using(app.appID).filter(subject__in=subject)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        app = models.get_target_app(self.request.user,
                                    appID=self.request.data['appID'] if 'appID' in self.request.data else None)
        if app==None:
            raise ValidationError({'info': 'App Not Found!', 'error_code': NO_APP_ERROR})
        if 'subjectID' not in self.request.data:
            raise ValidationError({'info': 'SubjectID is required.', 'error_code': INVALID_REQUEST_ERROR})

        subject = Subject.objects.using(app.appID).filter(subjectID=self.request.data['subjectID'])

        if len(subject) != 1: # have and only have one person
            log.error('No person specified!')
            raise ValidationError({'info': 'Unique subject id need to be given!', 'error_code': NO_SUBJECT_ERROR})

        image = None
        if 'image' not in self.request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'info': 'Image is required.', 'error_code': NO_IMAGE_ERROR})

        try:
            tmp_image = Image.open(self.request.data['image'])
            tmp_array = np.array(tmp_image)
            cv2.cvtColor(tmp_array, cv2.COLOR_RGB2BGR)
            image = self.request.data['image']
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'info': 'Image format error or data corrupted!', 'error_code': IMAGE_FORMAT_ERROR})

        face = serializer.save(subject=subject[0], image=image)
        subject[0].save() # this will update person's modified_time
        app.save() # this will update app's modified_time

        # calculate known features
        for name, func in self.feature_extractor.extractors.items():
            Feature.objects.db_manager(app.appID).create(feature_name=name, face=face, data=json.dumps(self.feature_extractor.extract(Image.open(self.request.data['image']), name).real.tolist()))

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        serializer.save(image=None if 'image' not in self.request.data else self.request.data['image'])


def service_bind(service_config):
    service = service_config[2]()
    def decorator(func):
        def func_wrapper(self, request):
            # find the app
            if 'appID' not in request.data or len(App.objects.filter(company=request.user, appID=request.data['appID']))==0:
                raise ValidationError({'info': 'App Not Found',  'error_code': NO_APP_ERROR})
                        # validation service input
            app = App.objects.filter(appID=request.data['appID'], company=request.user)[0]
            is_valid, info = service.is_valid_input_data(request.data, app=app)
            if not is_valid:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'info': info})
            return func(self, request, service, service_config[0], app)
        return func_wrapper
    return decorator


def log_command():
    def decorator(func):
        def func_wrapper(self, request, service, serviceID, app):
            # generate the command
            ret = Command.objects.create(company=request.user, app=app, serviceID=serviceID)
            ret.save()
            return func(self, request, service, app)
        return func_wrapper
    return decorator

class CommandViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = CommandSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        if self.request.user.is_superuser:
            commands = Command.objects.all()
            if 'companyID' in self.request.data:
                commands = commands.filter(company__id=self.request.data['companyID'])
            return commands
        else:
            return Command.objects.filter(company=self.request.user)

    # https://www.thecodeship.com/patterns/guide-to-python-function-decorators/
    @list_route(methods=['post', ], permission_classes=[TokenPermission, ])
    @service_bind(services.QUALITY_CHECK)
    @log_command()
    def quality_check(self, request, service, app):
        results = service.execute(data=request.data)
        log.info('Service: '+services.QUALITY_CHECK[1])
        return Response(results)

    @list_route(methods=['post', ], permission_classes=[TokenPermission, ])
    @service_bind(services.FACE_DETECTION)
    @log_command()
    def detect(self, request, service, app):
        results = service.execute(data=request.data, app=app)
        log.info("Service: "+services.FACE_DETECTION[1])
        return Response(results)

    @list_route(methods=['get', ], permission_classes=[TokenPermission, ])
    @service_bind(services.ENROLLMENT)
    @log_command()
    def enroll(self, request, service, app):
        results = service.execute(data=request.data, app=app)
        log.info("Service: "+services.ENROLLMENT[1])
        return Response(results)

    @list_route(methods=['post', ], permission_classes=[TokenPermission, ])
    @service_bind(services.RECOGNITION)
    @log_command()
    def recognize(self, request, service, app):
        results = service.execute(request=request, data=request.data, app=app)
        log.info("Service: "+services.RECOGNITION[1])
        return Response(results)

    @list_route(methods=['post', ], permission_classes=[TokenPermission, ])
    @service_bind(services.COMPARE)
    @log_command()
    def compare(self, request, service, app):
        results = service.execute(request=request, data=request.data, app=app)
        log.info("Service: "+services.COMPARE[1])
        return Response(results)

    @list_route(methods=['post', ], permission_classes=[TokenPermission, ])
    @service_bind(services.VERIFICATION)
    @log_command()
    def verify(self, request, service, app):
        results = service.execute(request=request, data=request.data, app=app)
        log.info("Service: "+services.VERIFICATION[1])
        return Response(results)
