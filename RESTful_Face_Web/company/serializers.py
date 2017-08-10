# root serializers
from rest_framework import serializers
# model
from django.contrib.auth.models import User
from .models import Person, Face, Command
# utils
from rest_framework.utils import model_meta
from rest_framework.compat import set_many
# service
from service import services

class CompanySerializer(serializers.ModelSerializer):
    companyID = serializers.CharField(source="first_name", read_only=True)
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'password', 'companyID')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        company = User(**validated_data)
        company.set_password(validated_data['password'])
        company.save(using='default')
        return company

    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                set_many(instance, attr, value)
            else:
                setattr(instance, attr, value)
        instance.save(using='default')
        return instance

class PersonSerializer(serializers.HyperlinkedModelSerializer):
    faces = serializers.HyperlinkedRelatedField(many=True, view_name='face-detail', read_only=True)

    class Meta:
        model = Person
        fields = ('id', 'url', 'userID', 'companyID', 'name', 'email', 'first_name', 'last_name', 'note' ,'created_time', 'modified_time', 'faces')
        read_only_fields = ('id', 'userID', 'companyID', 'created_time', 'modified_time')

    def create(self, validated_data):
        return Person.objects.db_manager(validated_data['companyID']).create(**validated_data)

    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                set_many(instance, attr, value)
            else:
                setattr(instance, attr, value)
        instance.save(using=instance.companyID)
        return instance

class FaceSerializer(serializers.HyperlinkedModelSerializer):
    #showcase

    class Meta:
        model = Face
        fields = ('id', 'url', 'person', 'feature', 'created_time', 'modified_time', 'image')
        read_only_fields = ('person', )

    # override to user company's database
    def create(self, validated_data):
        return Face.objects.db_manager(validated_data['person'].companyID).create(**validated_data)

    # override to use company's database
    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                set_many(instance, attr, value)
            else:
                setattr(instance, attr, value)
        instance.save(using=instance.person.companyID)
        return instance

class CommandSerializer(serializers.HyperlinkedModelSerializer):
    service = serializers.CharField(source='get_service_name')

    class Meta:
        model = Command
        fields = ('id', 'url', 'company', 'service', 'issue_time', 'arguments', 'results')
