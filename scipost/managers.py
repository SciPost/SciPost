__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import NORMAL_CONTRIBUTOR, NEWLY_REGISTERED, AUTHORSHIP_CLAIM_PENDING

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
    """Custom defined filters for the Contributor model."""

    def active(self):
        """Return all validated and vetted Contributors."""
        return self.filter(user__is_active=True, status=NORMAL_CONTRIBUTOR)

    def available(self):
        """Filter out the Contributors that have active unavailability periods."""
        return self.exclude(
            unavailability_periods__start__lte=today,
            unavailability_periods__end__gte=today)

    def awaiting_validation(self):
        """Filter Contributors that have not been validated by the user."""
        return self.filter(user__is_active=False, status=NEWLY_REGISTERED)

    def awaiting_vetting(self):
        """Filter Contributors that have not been vetted through."""
        return self.filter(user__is_active=True, status=NEWLY_REGISTERED)

    def fellows(self):
        """TODO: NEEDS UPDATE TO NEW FELLOWSHIP RELATIONS."""
        return self.filter(user__groups__name='Editorial College')


class UnavailabilityPeriodManager(models.Manager):
    def today(self):
        return self.filter(start__lte=today, end__gte=today)

    def future(self):
        return self.filter(end__gte=today)


class AuthorshipClaimQuerySet(models.QuerySet):
    def awaiting_vetting(self):
        return self.filter(status=AUTHORSHIP_CLAIM_PENDING)
