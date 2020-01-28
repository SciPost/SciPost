__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import permissions

from .models import EmailAccountAccess


class CanHandleStoredMessage(permissions.BasePermission):
    """
    Object-level permission on StoredMessage, specifying whether the user
    can take editing actions.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_admin:
            return True

        # Check, based on account accesses
        for access in request.user.email_account_accesses.filter(
                rights=EmailAccountAccess.CRUD):
            if ((access.account.email == obj.data.sender or
                 access.account.email in obj.data.recipients)
                and access.date_from < obj.datetimestamp
                and access.data_until > obj.datetimestamp):
                return True
        return False
