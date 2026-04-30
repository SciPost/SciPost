__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from functools import reduce
from itertools import chain
import re
from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import (
    F,
    Count,
    Q,
    Exists,
    ExpressionWrapper,
    IntegerField,
    OuterRef,
    QuerySet,
    Subquery,
    Value,
)
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
    TrigramSimilarity,
)
from django.utils import timezone

from common.utils.models import qs_duplicates_group_by_key
from ethics.managers import CoauthorshipExclusionPurpose
from ethics.models import ConflictOfInterest

from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from profiles.models import Profile


class ProfileQuerySet(QuerySet):
    def eponymous(self):
        return self.filter(is_anonymous=False)

    def anonymous(self):
        return self.filter(is_anonymous=True)

    def get_unique_from_email_or_None(self, email):
        try:
            return self.get(emails__email=email)
        except self.model.DoesNotExist:
            pass
        except self.model.MultipleObjectsReturned:
            pass
        return None

    def get_potential_duplicates(self) -> "Mapping[Any, list[Profile]]":
        """
        Returns a mapping of potential duplicate Profiles, keyed by the normalized full name.
        """
        return {
            group: list(items)
            for group, items in qs_duplicates_group_by_key(self, "full_name_normalized")
        }

    def potential_duplicates_of(self, profile: "Profile"):
        """
        Returns only potential duplicate Profiles of the specified Profile.
        """
        from merger.models import NonDuplicateMark

        profile_non_duplicates = NonDuplicateMark.objects.involving(profile)
        qs = (
            self.all()
            .filter(full_name_normalized=profile.full_name_normalized)
            .exclude(id__in=profile_non_duplicates)
            .exclude(id=profile.id)
        )

        return qs

    def specialties_overlap(self, specialties_slug_list):
        """
        Returns all Profiles whose specialties overlap with those specified in the slug list.

        This method is also separately implemented for Contributor and PotentialFellowship objects.
        """
        return self.filter(specialties__slug__in=specialties_slug_list)

    def annot_has_conflicts_of_interest_with(self, profile):
        """
        Annotates the queryset with a boolean indicating whether each Profile
        has a conflict of interest with the specified profile.
        """
        return self.annotate(
            has_conflict_of_interest=Exists(
                ConflictOfInterest.objects.filter(
                    Q(profile=OuterRef("pk"), related_profile=profile)
                    | Q(profile=profile, related_profile=OuterRef("pk"))
                )
            )
        )

    def annot_has_conflicts_of_interest_with_any(self, profiles):
        """
        Annotates the queryset with a boolean indicating whether each Profile
        has a conflict of interest with any of the specified profiles.
        """
        return self.annotate(
            has_conflict_of_interest=Exists(
                ConflictOfInterest.objects.filter(
                    Q(profile=OuterRef("pk"), related_profile__in=profiles)
                    | Q(profile__in=profiles, related_profile=OuterRef("pk"))
                )
            )
        )

    def annot_has_conflicts_of_interest_with_submission_authors(
        self,
        submission,
        purpose=CoauthorshipExclusionPurpose.TAKING_CHARGE,
    ):
        """
        Annotates the queryset with a boolean indicating whether each Profile
        has a conflict of interest with any of the authors of the specified submission.
        This also includes a boolean indicating whether the Profile is one of the authors.
        """
        submission_authors = submission.author_profiles.values_list(
            "profile__id", flat=True
        )
        return self.annotate(
            is_submission_author=Q(id__in=submission_authors),
            has_conflict_of_interest_with_submission_authors=Exists(
                ConflictOfInterest.objects.all()
                .annot_date_expiry(purpose)
                .valid_on_date()
                .filter(
                    Q(
                        profile=OuterRef("pk"),
                        related_profile__in=submission_authors,
                    )
                    | Q(
                        profile__in=submission_authors,
                        related_profile=OuterRef("pk"),
                    )
                )
                .annot_submission_exempted(submission)
                .exclude(submission_exempted=True)
            ),
            # The flag is an "OR" of the two flags above
            has_any_conflict_of_interest_with_submission=ExpressionWrapper(
                Q(is_submission_author=True)
                | Q(has_conflict_of_interest_with_submission_authors=True),
                output_field=models.BooleanField(),
            ),
        )

    def no_conflicts_of_interest_with(self, profile: "Profile"):
        """
        Returns all Profiles which have no conflicts of interest with the specified profile.
        """
        CI_profiles = ConflictOfInterest.objects.involving_profile(profile).values_list(
            "profile", "related_profile"
        )
        # Unpack the collection of id-two-tuples into two tuples of ids
        profile_CoI, related_CoI = tuple(zip(*CI_profiles)) or ((), ())

        return self.exclude(id__in=profile_CoI + related_CoI + (profile.id,))

    def without_conflicts_of_interest_against_submission_authors_of(
        self, submission, **kwargs
    ):
        """
        Returns all Fellowships whose profiles have no conflicts of interest with any of the authors of the specified submission.
        """
        return self.annot_has_conflicts_of_interest_with_submission_authors(
            submission, **kwargs
        ).filter(has_any_conflict_of_interest_with_submission=False)

    def search(self, query: str):
        qs = self
        all_terms: list[str] = re.split(r"\s+", query.strip())

        # Handle ORCID
        for term in all_terms:
            if re.match(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", term):
                qs = qs.filter(orcid_id=term)
                all_terms.remove(term)

        # Split terms into initials and words.
        # Initials are either single letters or short terms (<=2 characters).
        # Words are longer terms which are likely to be either name.
        initials: list[str] = []
        words: list[str] = []
        for term in all_terms:
            if group := re.match(r"^([A-Za-z]+)\.$", term):
                initials.append(group.group(1))
            elif len(term) <= 2:
                initials.append(term.strip(". ,;"))
            else:
                words.append(term)

        # Compute trigram similarity for each initial and sum them
        qs = qs.annotate(
            similarity=reduce(
                lambda x, y: x + y,
                (
                    TrigramSimilarity("first_name", initial)
                    + TrigramSimilarity("last_name", initial)
                    for initial in initials
                ),
                Value(1),
            )
        ).filter(similarity__gte=1)

        # Match initials at the start of the field or after a separator (space or hyphen)
        initials_regex = r"(^|\s|-)({})".format("|".join(map(re.escape, initials)))
        qs = qs.annotate(
            contains_initials=Q(full_name__unaccent__iregex=initials_regex)
        ).filter(contains_initials=True)

        # Early exit if there are no words to search for.
        # Likely garbage matches, but better than no matches at all.
        if not words:
            return qs.order_by("-similarity", "last_name", "first_name")

        qs = (
            qs.annotate(
                rank=SearchRank(
                    SearchVector("first_name") + SearchVector("last_name"),
                    SearchQuery(" ".join(words), search_type="websearch"),
                ),
                total_rank=F("similarity") * F("rank"),
            )
            .filter(total_rank__gt=1e-5)
            .order_by("-total_rank", "last_name", "first_name")
        )

        return qs


class ProfileEmailQuerySet(QuerySet):
    def still_valid(self):
        """
        Return ProfileEmails which are still valid.
        """
        return self.filter(still_valid=True)

    def primary(self):
        """
        Return ProfileEmails which are primary.
        """
        return self.filter(primary=True)

    def verified(self):
        """
        Return ProfileEmails which are verified.
        """
        return self.filter(verified=True)

    def recovery(self):
        """
        Return ProfileEmails which are recovery emails.
        """
        from profiles.models import ProfileEmail

        return self.filter(kind=ProfileEmail.KIND_RECOVERY)


class AffiliationQuerySet(QuerySet):
    def current(self):
        """
        Return affiliations which are currently valid.
        """
        today = timezone.now().date()
        return self.filter(
            Q(date_from__lte=today, date_until__isnull=True)
            | Q(date_from__isnull=True, date_until__gte=today)
            | Q(date_from__lte=today, date_until__gte=today)
            | Q(date_from__isnull=True, date_until__isnull=True)
        )
