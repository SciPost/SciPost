import datetime

from django.db import models
from django.db.models import Q

from .constants import CONTRIBUTOR_NORMAL, INVITATION_EDITORIAL_FELLOW,\
                       CONTRIBUTOR_NEWLY_REGISTERED


class FellowManager(models.Manager):
    def active(self, *args, **kwargs):
        today = datetime.date.today()
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True),
            **kwargs).order_by('contributor__user__last_name')


class ContributorManager(models.Manager):
    def active(self):
        return self.filter(user__is_active=True, status=CONTRIBUTOR_NORMAL)

    def awaiting_validation(self):
        return self.filter(user__is_active=False, status=CONTRIBUTOR_NEWLY_REGISTERED)

    def fellows(self):
        return self.filter(user__groups__name='Editorial College')


class RegistrationInvitationManager(models.Manager):
    def pending_invited_fellows(self):
        return self.filter(invitation_type=INVITATION_EDITORIAL_FELLOW,
                           responded=False, declined=False)

    def declined_invited_fellows(self):
        return self.filter(invitation_type=INVITATION_EDITORIAL_FELLOW,
                           responded=False, declined=True)


class UnavailabilityPeriodManager(models.Manager):
    def today(self):
        today = datetime.date.today()
        return self.filter(start__lte=today, end__gte=today)
