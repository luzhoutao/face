from django.shortcuts import render
# request and response
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework import status
# view
from rest_framework import viewsets, mixins
from rest_framework.decorators import permission_classes as permissionClasses
# serializers
from .serializers import CompanySerializer
# models
from django.contrib.auth.models import User

# permissions
from rest_framework import permissions
from .permissions import CompanyPermission, CompaniesPermission

# Create your views here.
class CompaniesViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (CompaniesPermission, )

class CompanyViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (CompanyPermission, )

    @detail_route(methods=['put'])
    def update_info(self, request, pk=None, *args, **kwargs):
        company = self.get_object()
        if not company:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.update(company,request.data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)






