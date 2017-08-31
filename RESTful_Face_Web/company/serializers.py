# root serializers
from rest_framework import serializers
# model
from django.contrib.auth.models import User
from .models import Subject, Face, Command, App, Token2Token
# utils
from rest_framework.utils import model_meta

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
            setattr(instance, attr, value)
        instance.save(using='default')
        return instance

class Token2TokenSerializer(serializers.ModelSerializer):
    duration = serializers.CharField(source='get_duration', read_only=True)
    class Meta:
        model = Token2Token
        fields = ('duration', 'company')
        read_only_fields = ('duration', 'company')

class SubjectSerializer(serializers.HyperlinkedModelSerializer):
    faces = serializers.HyperlinkedRelatedField(many=True, view_name='face-detail', read_only=True)

    class Meta:
        model = Subject
        fields = ('id', 'url', 'subjectID', 'appID', 'subject_name','faces')
        read_only_fields = ('id', 'subjectID', 'appID')

    def create(self, validated_data):
        return Subject.objects.db_manager(validated_data['appID']).create(**validated_data)

    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=instance.appID)
        return instance

class FaceSerializer(serializers.HyperlinkedModelSerializer):
    #showcase

    class Meta:
        model = Face
        fields = ('id', 'url', 'subject', 'created_time', 'modified_time', 'image')
        read_only_fields = ('subject', )

    # override to user company's database
    def create(self, validated_data):
        return Face.objects.db_manager(validated_data['subject'].appID).create(**validated_data)

    # override to use company's database
    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=instance.person.appID)
        return instance

class CommandSerializer(serializers.HyperlinkedModelSerializer):
    service = serializers.CharField(source='get_service_name')

    class Meta:
        model = Command
        fields = ('id', 'url', 'company', 'app', 'service', 'issue_time', 'arguments', 'results')

class AppSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.CharField(source="get_status", read_only=True)

    class Meta:
        model = App
        fields = ('id', 'url', 'company', 'app_name', 'status', 'appID', 'update_time')
        read_only_fields = ['company', 'appID', 'update_time']