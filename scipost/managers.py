__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import Concat, Lower
from django.utils import timezone

from .constants import NORMAL_CONTRIBUTOR, NEWLY_REGISTERED, AUTHORSHIP_CLAIM_PENDING


class FellowManager(models.Manager):
    def active(self):
        today = timezone.now().date()
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
        today = timezone.now().date()
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
        return self.filter(fellowships__isnull=False).distinct()

    def with_duplicate_names(self):
        """
        Returns only potential duplicate Contributors (as identified by first and
        last names).
        Admins and superusers are explicitly excluded.
        """
        contribs = self.active().exclude(user__is_superuser=True).exclude(user__is_staff=True
        ).annotate(full_name=Concat('user__last_name', 'user__first_name'))
        duplicates = contribs.values('full_name').annotate(
            nr_count=Count('full_name')).filter(nr_count__gt=1)
        return contribs.filter(full_name__in=[item['full_name'] for item in duplicates]
                              ).order_by('user__last_name', 'user__first_name', '-id')

    def with_duplicate_email(self):
        """
        Return Contributors having duplicate emails.
        """
        duplicates = self.active().exclude(user__is_superuser=True).exclude(user__is_staff=True
        ).values(lower_email=Lower('user__email')).annotate(
            Count('id')).order_by('user__last_name').filter(id__count__gt=1)
        return self.annotate(lower_email=Lower('user__email')
        ).filter(lower_email__in=[dup['lower_email'] for dup in duplicates])


class UnavailabilityPeriodManager(models.Manager):
    def today(self):
        today = timezone.now().date()
        return self.filter(start__lte=today, end__gte=today)

    def future(self):
        today = timezone.now().date()
        return self.filter(end__gte=today)


class AuthorshipClaimQuerySet(models.QuerySet):
    def awaiting_vetting(self):
        return self.filter(status=AUTHORSHIP_CLAIM_PENDING)
