__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import Concat, Lower
from django.utils import timezone


class ProfileQuerySet(models.QuerySet):
    def get_unique_from_email_or_None(self, email):
        try:
            return self.get(emails__email=email)
        except self.model.DoesNotExist:
            pass
        except self.model.MultipleObjectsReturned:
            pass
        return None

    def potential_duplicates(self):
        """
        Returns only potential duplicate Profiles (as identified by first and
        last names, and separately by (case-insensitive) email).
        """
        # Start by treating name duplicates, excluding marked Profile non-duplicates
        from .models import ProfileNonDuplicates

        profiles = self.annotate(full_name=Concat("last_name", "first_name"))
        nonduplicate_full_names = [
            dup.full_name for dup in ProfileNonDuplicates.objects.all()
        ]
        duplicates_by_full_name = (
            profiles.values("full_name")
            .annotate(nr_count=Count("full_name"))
            .filter(nr_count__gt=1)
            .exclude(full_name__in=nonduplicate_full_names)
        )
        from .models import ProfileEmail

        # Now for email duplicates. Because of case-insensitivity, we need some gymnastics
        pel = ProfileEmail.objects.annotate(email_lower=Lower("email"))
        # Build list of all duplicate lowercased emails
        duplicate_emails = [
            pe["email_lower"]
            for pe in pel.values("email_lower")
            .annotate(nel=Count("email_lower"))
            .filter(nel__gt=1)
        ]
        # Then determine all ids of related Profiles with an email in this list
        ids_of_duplicates_by_email = [
            pe.profile.id for pe in pel.filter(email_lower__in=duplicate_emails)
        ]
        # Now return list of potential duplicates
        return profiles.filter(
            models.Q(
                full_name__in=[item["full_name"] for item in duplicates_by_full_name]
            )
            | models.Q(id__in=ids_of_duplicates_by_email)
        ).order_by("last_name", "first_name", "-id")

    def specialties_overlap(self, specialties_slug_list):
        """
        Returns all Profiles whose specialties overlap with those specified in the slug list.

        This method is also separately implemented for Contributor and PotentialFellowship objects.
        """
        return self.filter(specialties__slug__in=specialties_slug_list)

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


class AffiliationQuerySet(models.QuerySet):
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
