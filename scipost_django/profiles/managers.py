__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import (
    Count,
    Q,
    Exists,
    ExpressionWrapper,
    OuterRef,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.functions import Concat, Lower
from django.utils import timezone

from ethics.models import CompetingInterest


class ProfileQuerySet(QuerySet):
    def get_unique_from_email_or_None(self, email):
        try:
            return self.get(emails__email=email)
        except self.model.DoesNotExist:
            pass
        except self.model.MultipleObjectsReturned:
            pass
        return None

    def with_full_names(self):
        return self.annotate(
            full_name_annot=Concat(
                Unaccent("first_name"),
                Value(" "),
                Unaccent("last_name"),
            )
        )

    def potential_duplicates(self):
        """
        Returns only potential duplicate Profiles (as identified by first and
        last names, and separately by (case-insensitive) email).
        """
        # Start by treating name duplicates, excluding marked Profile non-duplicates
        from .models import ProfileEmail

        profiles = self.with_full_names().filter(profilenonduplicates__isnull=True)

        duplicates_by_full_name = (
            profiles.values("full_name_annot")
            .annotate(nr_count=Count("full_name_annot"))
            .filter(nr_count__gt=1)
            .values("full_name_annot")
        )

        # Find Profiles whose email is used by another Profile
        ids_of_duplicates_by_email = (
            ProfileEmail.objects.annotate(
                used_by_another=Exists(
                    ProfileEmail.objects.filter(
                        ~Q(profile=OuterRef("profile")),
                        email__iexact=OuterRef("email"),
                    )
                )
            ).filter(used_by_another=True)
        ).values("profile")

        return profiles.filter(
            Q(full_name_annot__in=duplicates_by_full_name)
            | Q(id__in=ids_of_duplicates_by_email)
        ).order_by("last_name", "first_name", "-id")

    def specialties_overlap(self, specialties_slug_list):
        """
        Returns all Profiles whose specialties overlap with those specified in the slug list.

        This method is also separately implemented for Contributor and PotentialFellowship objects.
        """
        return self.filter(specialties__slug__in=specialties_slug_list)

    def annot_has_competing_interests_with(self, profile):
        """
        Annotates the queryset with a boolean indicating whether each Profile
        has a competing interest with the specified profile.
        """
        return self.annotate(
            has_competing_interest=Exists(
                CompetingInterest.objects.filter(
                    Q(profile=OuterRef("pk"), related_profile=profile)
                    | Q(profile=profile, related_profile=OuterRef("pk"))
                )
            )
        )

    def annot_has_competing_interests_with_any(self, profiles):
        """
        Annotates the queryset with a boolean indicating whether each Profile
        has a competing interest with any of the specified profiles.
        """
        return self.annotate(
            has_competing_interest=Exists(
                CompetingInterest.objects.filter(
                    Q(profile=OuterRef("pk"), related_profile__in=profiles)
                    | Q(profile__in=profiles, related_profile=OuterRef("pk"))
                )
            )
        )

    def annot_has_competing_interests_with_submission_authors(self, submission):
        """
        Annotates the queryset with a boolean indicating whether each Profile
        has a competing interest with any of the authors of the specified submission.
        This also includes a boolean indicating whether the Profile is one of the authors.
        """
        submission_authors = submission.author_profiles.values_list(
            "profile__id", flat=True
        )
        return (
            self.annotate(
                is_submission_author=Exists(
                    Subquery(submission_authors.filter(profile=OuterRef("pk")))
                )
            )
            .annotate(
                has_submission_competing_interests=Exists(
                    Subquery(
                        CompetingInterest.objects.filter(
                            Q(
                                profile=OuterRef("pk"),
                                related_profile__in=submission_authors,
                            )
                            | Q(
                                profile__in=submission_authors,
                                related_profile=OuterRef("pk"),
                            )
                        )
                    )
                )
            )
            .annotate(
                # The flag is an "OR" of the two flags above
                has_any_competing_interest_with_submission=ExpressionWrapper(
                    Q(is_submission_author=True)
                    | Q(has_submission_competing_interests=True),
                    output_field=models.BooleanField(),
                )
            )
        )

    def no_competing_interests_with(self, profile):
        """
        Returns all Profiles which have no competing interests with the specified profile.
        """
        CI_profiles = CompetingInterest.objects.involving_profile(profile).values_list(
            "profile", "related_profile"
        )
        # Unpack the collection of id-two-tuples into two tuples of ids
        profile_CI, related_CI = tuple(zip(*CI_profiles)) or ((), ())

        return self.exclude(id__in=profile_CI + related_CI)

    def without_competing_interests_against_submission_authors_of(self, submission):
        """
        Returns all Fellowships whose profiles have no competing interests with any of the authors of the specified submission.
        """
        return self.annot_has_competing_interests_with_submission_authors(
            submission
        ).filter(has_any_competing_interest_with_submission=False)

    def search(self, query):
        """
        Returns all Profiles matching the query for first name, last name, email, or ORCID.
        Exact matches are returned first, then partial matches.
        """
        terms = query.replace(",", "").split(" ")

        # Get ORCID term.
        orcid_term = Q()
        for i, term in enumerate(terms):
            if re.match(r"[\d-]+", term):
                terms.pop(i)
                orcid_term |= Q(orcid_id__icontains=term)

        # Get mail term.
        mail_term = Q()
        for i, term in enumerate(terms):
            if "@" in term:
                terms.pop(i)  # Remove mail from further processing.
                mail_term |= Q(emails__email__icontains=term)

        name_terms = terms

        base_query = mail_term & orcid_term

        exact_query = base_query
        exact_last_query = base_query
        exact_first_query = base_query
        contains_query = base_query

        exact_first = lambda name: Q(first_name__unaccent__iexact=name)
        exact_last = lambda name: Q(last_name__unaccent__iexact=name)
        contains_first = lambda name: Q(first_name__unaccent__icontains=name)
        contains_last = lambda name: Q(last_name__unaccent__icontains=name)

        for name in name_terms:
            # Find exact matches first where every word matches either first or last name.
            exact_query &= exact_first(name) | exact_last(name)

            # Find an exact match for the last name.
            exact_last_query &= contains_first(name) | exact_last(name)

            # Find an exact match for the first name.
            exact_first_query &= exact_first(name) | contains_last(name)

            # Find a contains match for the either name.
            contains_query &= contains_first(name) | contains_last(name)

        # If there are exact matches, do not include other matches.
        exact_profiles = self.filter(exact_query).distinct()
        if exact_profiles.count() > 0:
            return exact_profiles

        # If there are partial exact matches, do not include other matches.
        exact_first_profiles = self.filter(exact_first_query)
        exact_last_profiles = self.filter(exact_last_query)
        partial_exact_profiles = (exact_first_profiles | exact_last_profiles).distinct()
        if partial_exact_profiles.count() > 0:
            return partial_exact_profiles

        # Include profiles matching all (partial) words in either first or last name.
        contains_profiles = self.filter(contains_query).distinct()
        return contains_profiles


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
