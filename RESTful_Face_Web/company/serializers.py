# root serializers
from rest_framework import serializers
# model
from django.contrib.auth.models import User
from .models import Person
# utils
from .utils.random_unique_id import generate_unique_id
from .utils.retrieve_admin import get_admin

class CompanySerializer(serializers.ModelSerializer):
    companyID = serializers.CharField(source="first_name", read_only=True)
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'password', 'companyID')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['companyID'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class PersonSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'userID', 'companyID', 'name', 'email', 'first_name', 'last_name', 'note' ,'created_time', 'modified_time')
        read_only_fields = ('id', 'userID', 'companyID', 'created_time', 'modified_time')

