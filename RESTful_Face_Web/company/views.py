from django.shortcuts import render
# request and response
from rest_framework.response import Response
# view
from rest_framework import viewsets, mixins
# serializers
from .serializers import CompanySerializer, PersonSerializer
# models
from django.contrib.auth.models import User
from .models import Person
from RESTful_Face_Web.settings import DATABASES
# permissions
from rest_framework import permissions
from .permissions import CompanyPermission, CompaniesPermission

# utils
from .utils.random_unique_id import generate_unique_id
from .utils.retrieve_admin import get_admin
from .utils.runtime_database import create_database

class CompaniesViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = User.objects.using('default').all()
    serializer_class = CompanySerializer
    permission_classes = (CompaniesPermission, )

    def perform_create(self, serializer):
        print("TODO: create new database")
        serializer.save(companyID=generate_unique_id(get_admin()))
        create_database(serializer.data['companyID'])
        print(Person.objects.using(serializer.data['companyID']).all())

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
        return Response(serializer.data)

    def perform_destroy(self, instance):
        persons = Person.objects.filter(companyID=instance.first_name)
        [person.delete() for person in persons]
        instance.delete()

class PersonViewSet(viewsets.ModelViewSet):
    serializer_class = PersonSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        company = self.request.user
        return Person.objects.using(company.first_name).all()

    def perform_create(self, serializer):
        serializer.save(companyID=self.request.user.first_name, userID=generate_unique_id(self.request.user), )

    def update(self, request, *args, **kwargs):
        person = self.get_object()
        serializer = self.get_serializer(person, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
