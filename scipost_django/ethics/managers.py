__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import enum
import datetime

from django.db.models import F, Case, Exists, OuterRef, QuerySet, Q, When, fields
from django.db.models.functions import Coalesce
from django.utils import timezone

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from submissions.models.submission import Submission
    from profiles.models import Profile
    from .models import ConflictOfInterest, Coauthorship


class CoauthorshipExclusionPurpose(enum.Enum):
    """
    Enum for varying exclusion duration due to (coauthorship) conflicts of interest.
    According to current by-laws (2025), coauthorships lead to conflicts of interest
    for 5 years when taking charge, and 3 years when refereeing.
    """

    TAKING_CHARGE = "taking_charge"
    REFEREEING = "refereeing"

    @property
    def offset_years(self) -> int:
        match self:
            case self.TAKING_CHARGE:
                return 5
            case self.REFEREEING:
                return 3
            case _:
                raise ValueError("Unknown purpose")

    @property
    def offset_timedelta(self) -> datetime.timedelta:
        return datetime.timedelta(days=self.offset_years * 365)


class ConflictOfInterestQuerySet(QuerySet["ConflictOfInterest"]):
    def annot_date_expiry(self, purpose: CoauthorshipExclusionPurpose):
        """
        Annotate `date_expiry` as `date_from` + `offset_years` for the given purpose,
        when due to a coauthorship. Otherwise maintain hardcoded `date_until`.
        Keeps existing date_expiry if present.
        """
        return self.annotate(
            date_expiry=Case(
                When(
                    Q(nature=self.model.COAUTHOR),
                    then=Coalesce(
                        F("date_until"),
                        F("date_from") + purpose.offset_timedelta,
                        output_field=fields.DateField(),
                    ),
                ),
                default=F("date_until"),
            ),
        )

    def annot_submission_exempted(self, submission: "Submission"):
        """
        Annotate whether the given submission is to be exempted
        from these conflicts of interest.
        """
        return self.annotate(
            submission_exempted=Q(
                exempted_submission_threads__contains=[submission.thread_hash]
            )
        )

    def valid_on_date(self, date: datetime.date | None = None):
        """
        Filter for validity on given optional date.
        """
        if not date:
            date = timezone.now().date()

        # Calculate expiry date only if it hasn't yet been annotated
        if not self.query.annotations.get("date_expiry"):
            self = self.annot_date_expiry(CoauthorshipExclusionPurpose.TAKING_CHARGE)

        return self.filter(
            Q(date_from__lte=date, date_expiry__isnull=True)
            | Q(date_from__isnull=True, date_expiry__gte=date)
            | Q(date_from__lte=date, date_expiry__gte=date)
            | Q(date_from__isnull=True, date_expiry__isnull=True)
        ).order_by()

    def involving_any_submission_author_of(self, submission: "Submission"):
        """
        Filter for conflicts of interest involving any author of the given submission.
        """
        author_profile_ids = submission.author_profiles.values("profile")
        return self.filter(
            Q(profile__in=author_profile_ids)
            | Q(related_profile__in=author_profile_ids)
        )

    def involving_profile(self, profile: "Profile"):
        """
        Filter for conflicts of interest involving given Profile.
        """
        return self.filter(Q(profile=profile) | Q(related_profile=profile))

    def between_profile_sets(
        self,
        profile_id_set_1: list[int],
        profile_id_set_2: list[int],
    ):
        """
        Filter for conflicts of interest between two sets of Profiles.
        """
        return self.filter(
            Q(profile__in=profile_id_set_1, related_profile__in=profile_id_set_2)
            | Q(profile__in=profile_id_set_2, related_profile__in=profile_id_set_1)
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

    def involving_profiles(self, profiles: list["Profile"] | QuerySet["Profile"]):
        """
        Return all instances matching at least one of the given Profiles.
        """
        return self.filter(Q(profile__in=profiles) | Q(coauthor__in=profiles))

    def not_involving_profile(self, profile: "Profile"):
        """
        Filter for Coauthorships not involving given Profile.
        """
        return self.exclude(Q(profile=profile) | Q(coauthor=profile))

    def between_profiles(
        self,
        profile_set_1: "Profile | list[Profile] | QuerySet[Profile]",
        profile_set_2: "Profile | list[Profile] | QuerySet[Profile]",
    ):
        """
        Filter for Coauthorships between two Profiles or profile sets.
        """
        from profiles.models import Profile

        if isinstance(profile_set_1, Profile):
            profile_set_1 = [profile_set_1]
        if isinstance(profile_set_2, Profile):
            profile_set_2 = [profile_set_2]

        return self.filter(
            Q(profile__in=profile_set_1, coauthor__in=profile_set_2)
            | Q(profile__in=profile_set_2, coauthor__in=profile_set_1)
        )

    def involving_any_author_of(self, submission: "Submission"):
        """
        Return all instances involving any author of the given submission.
        """
        author_profile_ids = submission.author_profiles.values("profile")
        return self.filter(
            Q(profile__in=author_profile_ids) | Q(coauthor__in=author_profile_ids)
        )

    def involving_any_fellow_of(self, submission: "Submission"):
        """
        Return all instances involving any fellow of the given submission.
        """
        fellow_profile_ids = submission.fellows.values("contributor__profile")
        return self.filter(
            Q(profile__in=fellow_profile_ids) | Q(coauthor__in=fellow_profile_ids)
        )

    def duplicate_of(self, coauthorship: "Coauthorship"):
        """
        Return a duplicate of the given Coauthorship,
        i.e. with the same profile, coauthor and work but a different PK.
        """
        return (
            self.filter(
                profile=coauthorship.profile,
                coauthor=coauthorship.coauthor,
                work=coauthorship.work,
            )
            .exclude(pk=coauthorship.pk)
            .first()
        )
