__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Count
from django.db.models.functions import Concat


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
        last names).
        """
        from .models import ProfileNonDuplicates
        profiles = self.annotate(full_name=Concat('last_name', 'first_name'))
        nonduplicate_full_names = [dup.full_name for dup in ProfileNonDuplicates.objects.all()]
        duplicates = profiles.values('full_name').annotate(
            nr_count=Count('full_name')
        ).filter(nr_count__gt=1).exclude(full_name__in=nonduplicate_full_names)
        return profiles.filter(full_name__in=[item['full_name'] for item in duplicates]
                              ).order_by('last_name', 'first_name', '-id')
