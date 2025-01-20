from rest_framework.permissions import BasePermission
class IsAdmin(BasePermission):
    def has_permission(self,request,view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsAuthorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'author']

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'author':
            return obj.author == request.user
        return True
class IsCommenterOrAdmin(BasePermission):
    def has_object_permission(self,request,view,obj):
        return request.user == obj.commenter or request.user.role == "admin"