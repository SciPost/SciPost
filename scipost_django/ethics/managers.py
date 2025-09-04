__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db.models import QuerySet, Q
from django.utils import timezone

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from submissions.models.submission import Submission
    from profiles.models import Profile
    from .models import CompetingInterest, Coauthorship


class CompetingInterestQuerySet(models.QuerySet):
    def valid_on_date(self, date: datetime.date = None):
        """
        Filter for validity on given optional date.
        """
        if not date:
            date = timezone.now().date()
        return self.filter(
            Q(date_from__lte=date, date_until__isnull=True)
            | Q(date_from__isnull=True, date_until__gte=date)
            | Q(date_from__lte=date, date_until__gte=date)
            | Q(date_from__isnull=True, date_until__isnull=True)
        ).order_by()

    def involving_profile(self, profile):
        """
        Filter for CompetingInterests involving given Profile.
        """
        return self.filter(Q(profile=profile) | Q(related_profile=profile))

    def between_profile_sets(self, profile_set_1, profile_set_2):
        """
        Filter for CompetingInterests between two sets of Profiles.
        """
        return self.filter(
            Q(profile__in=profile_set_1, related_profile__in=profile_set_2)
            | Q(profile__in=profile_set_2, related_profile__in=profile_set_1)
)


class CoauthorshipQuerySet(QuerySet["Coauthorship"]):
    def unverified(self):
        return self.filter(status="unverified")

    def non_deprecated(self):
        return self.exclude(status="deprecated")

    def involving_profile(self, profile: "Profile"):
        """
        Return all instances for certain profile.
        """
        return self.filter(Q(profile=profile) | Q(coauthor=profile))

    def not_involving_profile(self, profile: "Profile"):
        """
        Filter for Coauthorships not involving given Profile.
        """
        return self.exclude(Q(profile=profile) | Q(coauthor=profile))

    def between_profiles(self, profile_1: "Profile", profile_2: "Profile"):
        """
        Filter for Coauthorships between two Profiles.
        """
        profile, coauthor = sorted([profile_1, profile_2], key=lambda p: p.id)
        return self.filter(profile=profile, coauthor=coauthor)

    def involving_any_author_of(self, submission: "Submission"):
        """
        Return all instances involving any author of the given submission.
        """
        author_profile_ids = submission.author_profiles.values("profile")
        return self.filter(
            Q(profile__in=author_profile_ids) | Q(coauthor__in=author_profile_ids)
        )
