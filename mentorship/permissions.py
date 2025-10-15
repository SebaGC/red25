from rest_framework.permissions import BasePermission

from .models import Dupla, User


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN


class IsMentor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.MENTOR


class IsMentee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.MENTEE


class IsDuplaParticipantOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Dupla):
            dupla = obj
        else:
            dupla = getattr(obj, 'dupla', None)
        if not dupla:
            return False
        user = request.user
        if user.role == User.Role.ADMIN:
            return True
        return dupla.mentor_id == user.id or dupla.mentee_id == user.id

    def has_permission(self, request, view):
        return request.user.is_authenticated
