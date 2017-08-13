# url
from django.conf.urls import url, include
# router
from rest_framework.routers import DefaultRouter
# view
from .views import CompanyViewSet, CompaniesViewSet, PersonViewSet, FaceViewSet, CommandViewSet, AppViewSet

router = DefaultRouter()
router.register(r'companies', CompaniesViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'persons', PersonViewSet, base_name='person')
router.register(r'faces', FaceViewSet, base_name='face')
router.register(r'commands', CommandViewSet, base_name='command')
router.register(r'apps', AppViewSet, base_name='app')

urlpatterns = [
    url(r'^', include(router.urls)),
]