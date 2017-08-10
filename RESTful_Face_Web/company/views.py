from django.shortcuts import render
# request and response
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
# view
from rest_framework import viewsets, mixins
# parser
from rest_framework.parsers import MultiPartParser, FormParser
# serializers
from .serializers import CompanySerializer, PersonSerializer, FaceSerializer
# models
from django.contrib.auth.models import User
from .models import Person, Face
from django.db.models import Q
from RESTful_Face_Web.settings import DATABASES
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
# image
from PIL import Image
from io import BytesIO

class CompaniesViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = User.objects.using('default').all()
    serializer_class = CompanySerializer
    permission_classes = (CompaniesPermission, )

    def perform_create(self, serializer):
        serializer.save(first_name=generate_unique_id(get_admin()))

        log.info("Creating db for company %s (%s)..."%(serializer.data['username'], serializer.data['companyID']))
        myDBManager.create_database(serializer.data['companyID'])
        myDBManager.create_table(serializer.data['companyID'], Person, 'person')
        myDBManager.create_table(serializer.data['companyID'], Face, 'face')

        log.info("Company '%s' created !"%(serializer.data['username']))

# due to special permission requirement, splite list/create with CRUD on single object
class CompanyViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
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
        persons = Person.objects.filter(companyID=instance.first_name)
        [person.delete() for person in persons]

        myDBManager.drop_database(instance.first_name)
        log.info("Company '%s' destroyed!" % (instance.username))

        instance.delete()

class PersonViewSet(viewsets.ModelViewSet):
    serializer_class = PersonSerializer
    permission_classes = (permissions.IsAuthenticated, )

    # override to using specific database
    def get_queryset(self):
        company = self.request.user
        return Person.objects.using(company.first_name).all()

    # override to pass generated random ID
    def perform_create(self, serializer):
        serializer.save(companyID=self.request.user.first_name, userID=generate_unique_id(self.request.user), )
        log.info("Company %s(%s): user %s(%s) created!" % (self.request.user.username, self.request.user.first_name, serializer.data['name'], serializer.data['userID']))
    
    # override to do partial update
    def update(self, request, *args, **kwargs):
        person = self.get_object()
        serializer = self.get_serializer(person, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        log.info("Company %s(%s): user %s(%s) updated!" % (self.request.user.username, self.request.user.first_name, serializer.data['name'], serializer.data['userID']))
        return Response(serializer.data)

class FaceViewSet(viewsets.ModelViewSet):
    serializer_class = FaceSerializer
    permission_classes = (permissions.IsAuthenticated, )
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # get the person
        person = self.__get_person(self.request.user, self.request.data)
        print(Face.objects.using(self.request.user.first_name))
        # get person's all faces
        return Face.objects.using(self.request.user.first_name).filter(person__in=person)

    def perform_create(self, serializer):
        person = self.__get_person(self.request.user, self.request.data)
        if len(person) != 1:
            log.error('No person specified!')
            raise ValidationError({'FaceViewSet': 'No person specified!'})

        serializer.save(person=person[0], image=None if 'image' not in self.request.data else self.request.data['image'])

    def perform_update(self, serializer):
        serializer.save(image=None if 'image' not in self.request.data else self.request.data['image'])

    def __get_person(self, company, data):
        person = Person.objects.using(company.first_name)
        if 'name' in self.request.data:
            person = person.filter(name=self.request.data['name'])
        elif 'userID' in self.request.data:
            person = person.filter(userID=self.request.data['userID'])

        return [p for p in person]