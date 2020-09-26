__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Count
from django.db.models.functions import Concat, Lower


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
        profiles = self.annotate(full_name=Concat('last_name', 'first_name'))
        nonduplicate_full_names = [dup.full_name for dup in ProfileNonDuplicates.objects.all()]
        duplicates_by_full_name = profiles.values('full_name').annotate(
            nr_count=Count('full_name')).filter(nr_count__gt=1
            ).exclude(full_name__in=nonduplicate_full_names)
        from .models import ProfileEmail
        # Now for email duplicates. Because of case-insensitivity, we need some gymnastics
        pel = ProfileEmail.objects.annotate(email_lower=Lower('email'))
        # Build list of all duplicate lowercased emails
        duplicate_emails = [pe['email_lower'] for pe in pel.values('email_lower').annotate(
            nel=Count('email_lower')).filter(nel__gt=1)]
        # Then determine all ids of related Profiles with an email in this list
        ids_of_duplicates_by_email = [pe.profile.id for pe in pel.filter(
            email_lower__in=duplicate_emails)]
        # Now return list of potential duplicates
        return profiles.filter(
            models.Q(full_name__in=[item['full_name'] for item in duplicates_by_full_name]) |
            models.Q(id__in=ids_of_duplicates_by_email)
        ).order_by('last_name', 'first_name', '-id')
