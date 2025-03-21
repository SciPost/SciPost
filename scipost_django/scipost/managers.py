__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import Concat, Lower
from django.utils import timezone

from .constants import (
    NORMAL_CONTRIBUTOR,
    NEWLY_REGISTERED,
    DOUBLE_ACCOUNT,
    AUTHORSHIP_CLAIM_PENDING,
)


class ContributorQuerySet(models.QuerySet):
    """Custom defined filters for the Contributor model."""

    def eponymous(self):
        return self.filter(is_anonymous=False)

    def anonymous(self):
        return self.filter(is_anonymous=True)

    def active(self):
        """Return all validated and vetted Contributors."""
        return self.filter(user__is_active=True, status=NORMAL_CONTRIBUTOR)

    def nonduplicates(self):
        """
        Filter out duplicate Contributors.
        """
        return self.exclude(duplicate_of__isnull=False)

    def available(self):
        """Filter out the Contributors that have active unavailability periods."""
        today = timezone.now().date()
        return self.exclude(
            unavailability_periods__start__lte=today,
            unavailability_periods__end__gte=today,
        )

    def awaiting_validation(self):
        """Filter Contributors that have not been validated by the user."""
        return self.filter(user__is_active=False, status=NEWLY_REGISTERED)

    def awaiting_vetting(self):
        """Filter Contributors that have not been vetted through."""
        return self.filter(user__is_active=True, status=NEWLY_REGISTERED).exclude(
            status=DOUBLE_ACCOUNT
        )

    def with_duplicate_names(self):
        """
        Returns only potential duplicate Contributors (as identified by first and
        last names).
        Admins and superusers are explicitly excluded.
        """
        contribs = (
            self.exclude(status=DOUBLE_ACCOUNT)
            .exclude(user__is_superuser=True)
            .exclude(user__is_staff=True)
            .exclude(profile__isnull=True)
            .annotate(
                full_name=Concat(
                    Unaccent("profile__last_name"),
                    Unaccent("profile__first_name"),
                )
            )
        )
        duplicates = (
            contribs.values("full_name")
            .annotate(nr_count=Count("full_name"))
            .filter(nr_count__gt=1)
            .values_list("full_name", flat=True)
        )
        return contribs.filter(full_name__in=duplicates).order_by("full_name", "-id")

    def with_duplicate_email(self):
        """
        Return Contributors having duplicate emails.
        """
        qs = (
            self.exclude(status=DOUBLE_ACCOUNT)
            .exclude(user__is_superuser=True)
            .exclude(user__is_staff=True)
            .exclude(user__email="")
            .annotate(lower_email=Lower("user__email"))
        )
        duplicates = (
            qs.values("lower_email")
            .annotate(Count("id"))
            .filter(id__count__gt=1)
            .values_list("lower_email", flat=True)
        )
        return qs.filter(lower_email__in=duplicates)

    def specialties_overlap(self, specialties_slug_list):
        """
        Returns all Contributors whose specialties overlap with those specified in the slug list.

        This method is also separately implemented for Profile and PotentialFellowship objects.
        """
        return self.filter(profile__specialties__slug__in=specialties_slug_list)


class ContributorManager(models.Manager.from_queryset(ContributorQuerySet)):
    def get_queryset(self):
        return super().get_queryset().eponymous()


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
