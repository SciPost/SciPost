__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from itertools import chain
from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import Concat, Lower
from django.utils import timezone

from common.utils.models import qs_duplicates_group_by_key

from .constants import (
    NORMAL_CONTRIBUTOR,
    NEWLY_REGISTERED,
    DOUBLE_ACCOUNT,
    AUTHORSHIP_CLAIM_PENDING,
)

from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from profiles.models import Profile


class ContributorQuerySet(models.QuerySet):
    """Custom defined filters for the Contributor model."""

    def eponymous(self):
        return self.filter(is_anonymous=False)

    def anonymous(self):
        return self.filter(is_anonymous=True)

    def active(self):
        """Return all validated and vetted Contributors."""
        return self.filter(dbuser__is_active=True, status=NORMAL_CONTRIBUTOR)

    def get_potential_duplicates(self) -> "Mapping[Any, list[Profile]]":
        return {
            group: list(items)
            for group, items in chain(
                qs_duplicates_group_by_key(
                    self.select_related("profile"),
                    "profile__full_name_normalized",
                ),
                qs_duplicates_group_by_key(
                    self.select_related("dbuser").annotate(
                        lower_email=Lower("dbuser__email")
                    ),
                    "lower_email",
                ),
            )
        }

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
        return self.filter(dbuser__is_active=False, status=NEWLY_REGISTERED)

    def awaiting_vetting(self):
        """Filter Contributors that have not been vetted through."""
        return self.filter(dbuser__is_active=True, status=NEWLY_REGISTERED).exclude(
            status=DOUBLE_ACCOUNT
        )

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
