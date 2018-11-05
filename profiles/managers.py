__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
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
        profiles = self.annotate(full_name=Concat('last_name', 'first_name'))
        duplicates = profiles.values('full_name').annotate(
            nr_count=Count('full_name')
        ).filter(nr_count__gt=1)
        return profiles.filter(full_name__in=[item['full_name'] for item in duplicates]
                              ).order_by('last_name', 'first_name', '-id').remove_nonduplicates()

    def remove_nonduplicates(self):
        """
        To be called by self.potential_duplicates (in view of ordering assumptions).
        Recursively remove the leading profiles with same first and last name
        from the queryset, if they are found in a ProfileNonDuplicate instance.
        """
        from .models import ProfileNonDuplicates
        first_name_0 = self[0].first_name
        last_name_0 = self[0].last_name
        head = self.filter(first_name=first_name_0, last_name=last_name_0)
        print('Length of head is %s' % head.count())
        if ProfileNonDuplicates.objects.filter(profiles__in=head).exists():
            # Remove the head, call recursively
            print('Old queryset length: %s' % self.count())
            qs = self.difference(head)
            # return qs.order_by('last_name', 'first_name', '-id').remove_nonduplicates()
            print('New queryset length: %s' % qs.count())
            return qs.potential_duplicates()
        return self
