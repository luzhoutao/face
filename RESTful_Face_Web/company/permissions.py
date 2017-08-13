from rest_framework import permissions

class IsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class CompaniesPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        anonymous = request.user and request.user.is_anonymous
        superuser = request.user and request.user.is_superuser
        return ((anonymous or not superuser) and request.method == 'POST') or (superuser)

class CompanyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        :param request: 
        :param view: 
        :param obj:  instance of User
        :return: 
            company itself can retrieve, update
            admin can retrieve, delete
            other company no rights
            anonymous no permission
        """
        superuser = request.user and request.user.is_superuser
        owner = request.user and request.user == obj

        update = request.method in ['POST', 'PUT']
        delete = request.method == 'DELETE'
        safe = request.method in permissions.SAFE_METHODS

        return (superuser and (delete or safe)) or (owner and (safe or update))


