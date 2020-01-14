__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class StoredMessageQuerySet(models.QuerySet):
    """
    All StoredMessage querysets are always filtered for the user.
    """
    def filter_for_user(self, user, email):
        """
        Either su or staff, or user's email account accesses overlap with sender/recipients.
        """
        if not user.is_authenticated:
            return self.none()
        elif user.is_superuser or user.is_admin:
            return self

        # Filter based on account accesses
        if user.email_account_accesses.filter(account__email=email).exists():
            queryfilter = models.Q()
            for access in user.email_account_accesses.filter(account__email=email):
                print("access found: %s" % access.account.email)
                queryfilter = queryfilter | (
                    (models.Q(data__sender__icontains=access.account.email) |
                     models.Q(data__recipients__icontains=access.account.email))
                    & models.Q(datetimestamp__gt=access.date_from)
                    & models.Q(datetimestamp__lt=access.date_until)
                )
            return self.filter(queryfilter)
        return self.none()
