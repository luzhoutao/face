# root serializers
from rest_framework import serializers
# model
from django.contrib.auth.models import User
# utils
from .utils import generate_unique_id

class CompanySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'password', )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=generate_unique_id(),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user