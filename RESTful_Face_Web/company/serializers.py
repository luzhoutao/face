# root serializers
from rest_framework import serializers
# model
from django.contrib.auth.models import User
from .models import Person
# utils
from rest_framework.utils import model_meta
from rest_framework.compat import set_many

class CompanySerializer(serializers.ModelSerializer):
    companyID = serializers.CharField(source="first_name", read_only=True)
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'password', 'companyID')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        company = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['companyID'],
        )
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

class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'url', 'userID', 'companyID', 'name', 'email', 'first_name', 'last_name', 'note' ,'created_time', 'modified_time')
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