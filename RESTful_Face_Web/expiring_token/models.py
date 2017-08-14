from django.db import models
from rest_framework.authtoken.models import Token
from django.utils import timezone

# Create your models here.

class ExpiringToken(Token):
    expired_time = models.DateTimeField(null=True)

    def expired(self):
        """Return boolean indicating token expiration."""
        return timezone.now() > self.expired_time