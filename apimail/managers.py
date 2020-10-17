__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models


class DomainQuerySet(models.QuerySet):
    def active(self):
        from apimail.models import Domain
        return self.filter(status=Domain.STATUS_ACTIVE)


class EmailAccountAccessQuerySet(models.QuerySet):
    def current(self):
        today = datetime.date.today()
        return self.filter(date_from__lt=today, date_until__gt=today)
    def can_send(self):
        return self.filter(rights='CRUD')


class ComposedMessageQuerySet(models.QuerySet):
    """
    All ComposedMessage querysets are always filtered for the user.
    """
    def filter_for_user(self, user):
        return self.filter(author=user)

    def ready(self):
        return self.filter(status='ready')


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
        elif (user.is_superuser or user.is_staff) and email is None:
            return self

        # Filter based on account accesses
        if user.email_account_accesses.filter(account__email=email).exists():
            queryfilter = models.Q()
            for access in user.email_account_accesses.filter(account__email=email):
                queryfilter = queryfilter | (
                    (models.Q(data__sender__icontains=access.account.email) |
                     models.Q(data__recipients__icontains=access.account.email))
                    & models.Q(datetimestamp__gt=access.date_from)
                    & models.Q(datetimestamp__lt=access.date_until)
                )
            return self.filter(queryfilter)
        return self.none()
