__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import permissions

from .models import EmailAccountAccess


class CanHandleComposedMessage(permissions.BasePermission):
    """
    Object-level permission on ComposedMessage, specifying whether the user
    can take editing actions: is either admin or owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        return obj.author == request.user


class CanHandleStoredMessage(permissions.BasePermission):
    """
    Object-level permission on StoredMessage, specifying whether the user
    can take editing actions: is either admin or owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check, based on account accesses
        for access in request.user.email_account_accesses.filter(
            rights=EmailAccountAccess.CRUD
        ):
            if (
                (
                    access.account.email == obj.data["sender"]
                    or access.account.email in obj.data["recipients"]
                )
                and access.date_from < obj.datetimestamp.date()
                and access.date_until > obj.datetimestamp.date()
            ):
                return True
        return False


class CanReadStoredMessage(permissions.BasePermission):
    """
    Object-level permission on StoredMessage, specifying whether the user
    can read a StoredMessage instance.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check, based on account accesses
        for access in request.user.email_account_accesses.all():
            if (
                (
                    access.account.email == obj.data["sender"]
                    or access.account.email in obj.data["recipients"]
                )
                and access.date_from < obj.datetimestamp.date()
                and access.date_until > obj.datetimestamp.date()
            ):
                return True
        return False
