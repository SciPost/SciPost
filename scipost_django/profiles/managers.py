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

        profiles = self.with_full_names()
        nonduplicate_full_names = [
            dup.full_name for dup in ProfileNonDuplicates.objects.all()
        ]
        duplicates_by_full_name = (
            profiles.values("full_name_annot")
            .annotate(nr_count=Count("full_name_annot"))
            .filter(nr_count__gt=1)
            .exclude(full_name_annot__in=nonduplicate_full_names)
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
