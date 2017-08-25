# view
from rest_framework import viewsets, mixins
# model
from expiring_token.models import ExpiringToken
from company.models import Token2Token
# serializer
from expiring_token.serializers import TokenSerializer
# permissions
from rest_framework.permissions import IsAuthenticated
# time
from django.utils import timezone

# Create your views here.

class TokenViewSet(mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = TokenSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        company = self.request.user # either with username/password or token

        [token.delete() for token in ExpiringToken.objects.filter(user=company) if token.expired()]
        token = ExpiringToken.objects.filter(user=company)
        token2token = Token2Token.objects.filter(company=company,)

        print(len(token2token), len(token))

        if len(token) == 0 and len(token2token) == 1:
            self.generate_token(token2token, user=company)
            return ExpiringToken.objects.filter(user=company)

        if len(token) != 0:
            assert(len(token)==1)
            return token

    def generate_token(self, token2token, user):
        assert(len(token2token)==1)
        token2token = token2token[0]

        lifespan = token2token.duration
        expired_time = timezone.localtime(timezone.now()) + lifespan

        token = ExpiringToken.objects.create(user=user)
        token.expired_time = expired_time
        token.save()

        token2token.delete()