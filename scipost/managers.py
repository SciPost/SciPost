from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import CONTRIBUTOR_NORMAL, CONTRIBUTOR_NEWLY_REGISTERED, AUTHORSHIP_CLAIM_PENDING

today = timezone.now().date()


class FellowManager(models.Manager):
    def active(self):
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True)
            ).order_by('contributor__user__last_name')


class ContributorQuerySet(models.QuerySet):
    def active(self):
        return self.filter(user__is_active=True, status=CONTRIBUTOR_NORMAL)

    def available(self):
        return self.exclude(
            unavailability_periods__start__lte=today,
            unavailability_periods__end__gte=today)

    def awaiting_validation(self):
        return self.filter(user__is_active=False, status=CONTRIBUTOR_NEWLY_REGISTERED)

    def awaiting_vetting(self):
        return self.filter(user__is_active=True, status=CONTRIBUTOR_NEWLY_REGISTERED)

    def fellows(self):
        return self.filter(user__groups__name='Editorial College')


class UnavailabilityPeriodManager(models.Manager):
    def today(self):
        return self.filter(start__lte=today, end__gte=today)

    def future(self):
        return self.filter(end__gte=today)


class AuthorshipClaimQuerySet(models.QuerySet):
    def awaiting_vetting(self):
        return self.filter(status=AUTHORSHIP_CLAIM_PENDING)
