_copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import pytz

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ..managers import EmailAccountAccessQuerySet


class EmailAccount(models.Model):
    """
    Email account.

    Access is specified on a per-user basis through the related EmailAccountAccess model.
    """
    domain = models.ForeignKey(
        'apimail.Domain',
        related_name='email_accounts',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    description = models.TextField()

    class Meta:
        ordering = ['email',]

    def __str__(self):
        return('%s <%s>' % (self.name, self.email))

    def clean(self):
        if self.email.rpartition('@')[2] != self.domain.name:
            raise ValidationError("Email domain does not match domain name.")


class EmailAccountAccess(models.Model):
    """
    Access specifier for an email account, pertaining to a given User over a stated time window.

    We relate this to User instead of Contributor since we want to also cover
    Contacts, ProductionUsers and other Employees.

    This class is used for example to give access to internally-owned email addresses
    to specific employees for specific periods of employment.
    """
    CRUD = 'CRUD'
    READ = 'read'
    RIGHTS_CHOICES = (
        (CRUD, 'Can take all actions for this email account'),
        (READ, 'Can only view emails from/to this email account')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='email_account_accesses',
        on_delete=models.CASCADE)
    account = models.ForeignKey(
        'apimail.EmailAccount',
        related_name='accesses',
        on_delete=models.CASCADE)
    rights = models.CharField(max_length=8, choices=RIGHTS_CHOICES)
    date_from = models.DateField()
    date_until = models.DateField()

    objects = EmailAccountAccessQuerySet.as_manager()

    class Meta:
        ordering = ['account__email', 'user__last_name', '-date_until',]
