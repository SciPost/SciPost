__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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

    def with_full_names(self):
        return self.annotate(full_name_annot=Concat("first_name", "last_name"))

    def potential_duplicates(self):
        """
        Returns only potential duplicate Profiles (as identified by first and
        last names, and separately by (case-insensitive) email).
        """
        # Start by treating name duplicates, excluding marked Profile non-duplicates
        from .models import ProfileNonDuplicates

        profiles = self.with_full_names().exclude(
            id__in=ProfileNonDuplicates.objects.values_list("profiles", flat=True)
        )
        duplicates_by_full_name = (
            profiles.values("full_name_annot")
            .annotate(nr_count=Count("full_name_annot"))
            .filter(nr_count__gt=1)
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
                full_name_annot__in=[
                    item["full_name_annot"] for item in duplicates_by_full_name
                ]
            )
            | models.Q(id__in=ids_of_duplicates_by_email)
        ).order_by("last_name", "first_name", "-id")

    def specialties_overlap(self, specialties_slug_list):
        """
        Returns all Profiles whose specialties overlap with those specified in the slug list.

        This method is also separately implemented for Contributor and PotentialFellowship objects.
        """
        return self.filter(specialties__slug__in=specialties_slug_list)

    def no_competing_interests_with(self, profile):
        """
        Returns all Profiles which have no competing interests with the specified profile.
        """
        from ethics.models import CompetingInterest

        CI_profiles = CompetingInterest.objects.involving_profile(profile).values_list(
            "profile", "related_profile"
        )
        # Unpack the list of two-tuples into two lists
        profile_CI, related_CI = list(zip(*CI_profiles)) or ([], [])

        return self.exclude(id__in=profile_CI + related_CI)


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
