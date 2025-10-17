__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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
from django.db.models.functions import Cast, Concat, Lower
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
        """
        Returns all Profiles matching the query for first name, last name, email, or ORCID.
        Exact matches are returned first, then partial matches.
        """
        from profiles.models import ProfileEmail

        terms = [
            t
            for term in query.replace(",", " ").replace(";", " ").split()
            if (t := term.strip())
        ]

        # Get ORCID term.
        orcid_term = Q(pk__isnull=True)
        for i, term in enumerate(terms):
            if re.match(r"[\d-]+", term):
                terms.pop(i)
                orcid_term = Q(orcid_id__contains=term)

        # Remove dots from names to allow for matching initials
        name_terms = list(chain.from_iterable(term.split(".") for term in terms))
        name_terms = [t for term in name_terms if (t := term.strip())]

        # Set to impossible query if no name terms are present.
        base_query = Q() if len(name_terms) > 0 else Q(pk__isnull=True)

        exact_query = base_query
        exact_last_query = base_query
        exact_first_query = base_query
        contains_query = base_query
        mail_query = base_query

        exact_first = lambda name: Q(first_name__unaccent__iexact=name)
        exact_last = lambda name: Q(last_name__unaccent__iexact=name)
        contains_first = lambda name: Q(first_name__unaccent__icontains=name)
        contains_last = lambda name: Q(last_name__unaccent__icontains=name)
        contains_mail = lambda name: Q(email__icontains=name)

        for name in name_terms:
            # Find exact matches first where every word matches either first or last name.
            exact_query &= exact_first(name) | exact_last(name)

            # Find an exact match for the last name.
            exact_last_query &= contains_first(name) | exact_last(name)

            # Find an exact match for the first name.
            exact_first_query &= exact_first(name) | contains_last(name)

            # Find a contains match for the either name.
            contains_query &= contains_first(name) | contains_last(name)

            # Find a contains match for the email.
            mail_query &= contains_mail(name)

        return (
            self.annotate(
                exact_both=exact_query,
                exact_first=exact_first_query,
                exact_last=exact_last_query,
                contains=contains_query,
                matches_orcid=orcid_term,
                matches_email=Exists(
                    ProfileEmail.objects.filter(Q(profile=OuterRef("pk")) & mail_query)
                ),
                points=8 * Cast(F("exact_both"), output_field=IntegerField())
                + 3 * Cast(F("exact_first"), output_field=IntegerField())
                + 3 * Cast(F("exact_last"), output_field=IntegerField())
                + 1 * Cast(F("contains"), output_field=IntegerField())
                + 2 * Cast(F("matches_orcid"), output_field=IntegerField())
                + 2 * Cast(F("matches_email"), output_field=IntegerField()),
            )
            .filter(points__gt=0)
            .order_by("-points", "last_name", "first_name")
        )


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


class ProfileManager(models.Manager.from_queryset(ProfileQuerySet)):
    def get_queryset(self):
        return super().get_queryset().eponymous()
