from rest_framework import serializers
from expiring_token.models import ExpiringToken

class TokenSerializer(serializers.ModelSerializer):
    expired_time = serializers.CharField(source='get_expired_time', read_only=True)
    class Meta:
        model = ExpiringToken
        fields = ('expired_time', 'key')
        read_only_fields = ('expired_time', 'key')