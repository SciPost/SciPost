__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Q
from django.utils import timezone

today = timezone.now().date()


class AffiliationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            Q(begin_date__lte=today, end_date__isnull=True) |
            Q(begin_date__isnull=True, end_date__gte=today) |
            Q(begin_date__lte=today, end_date__gte=today) |
            Q(begin_date__isnull=True, end_date__isnull=True))

class InstitutionQuerySet(models.QuerySet):
    def has_publications(self):
        return self.filter(publications__isnull=False)
