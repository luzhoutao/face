# url
from django.conf.urls import url, include
# router
from rest_framework.routers import DefaultRouter
# view
from .views import CompanyViewSet, CompaniesViewSet, SubjectViewSet, FaceViewSet, CommandViewSet, AppViewSet
# doc
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer

router = DefaultRouter()
router.register(r'companies', CompaniesViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'subjects', SubjectViewSet, base_name='subject')
router.register(r'faces', FaceViewSet, base_name='face')
router.register(r'commands', CommandViewSet, base_name='command')
router.register(r'apps', AppViewSet, base_name='app')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'rest-api/', get_schema_view(title='Face API', renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer]), name='docs'),
]
