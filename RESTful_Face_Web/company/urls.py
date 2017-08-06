# url
from django.conf.urls import url, include
# router
from rest_framework.routers import DefaultRouter
# view
from .views import CompanyViewSet, CompaniesViewSet

router = DefaultRouter()
router.register(r'companies', CompaniesViewSet)
router.register(r'company', CompanyViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]