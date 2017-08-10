# url
from django.conf.urls import url, include
# router
from rest_framework.routers import DefaultRouter
# view
from .views import CompanyViewSet, CompaniesViewSet, PersonViewSet, FaceViewSet

router = DefaultRouter()
router.register(r'company', CompaniesViewSet)
router.register(r'company', CompanyViewSet)
router.register(r'person', PersonViewSet, base_name='person')
router.register(r'face', FaceViewSet, base_name='face')

urlpatterns = [
    url(r'^', include(router.urls)),
]