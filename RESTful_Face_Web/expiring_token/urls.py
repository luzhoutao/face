# url
from django.conf.urls import url, include
# router
from rest_framework.routers import DefaultRouter
# view
from expiring_token.views import TokenViewSet

router = DefaultRouter()
router.register(r'token', TokenViewSet, base_name='expiringtoken')

urlpatterns = [
    url(r'^', include(router.urls)),
]