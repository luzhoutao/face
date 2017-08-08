# url
from django.conf.urls import url, include
# router
from rest_framework.routers import DefaultRouter
# view
from .views import CompanyViewSet, CompaniesViewSet, PersonViewSet

router = DefaultRouter()
router.register(r'company', CompaniesViewSet)
router.register(r'company', CompanyViewSet)
router.register(r'persons', PersonViewSet, base_name='person')

urlpatterns = [
    url(r'^', include(router.urls)),
]