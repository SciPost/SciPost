import datetime

from django.db import models
from django.db.models import Q


class AffiliationQuerySet(models.QuerySet):
    def active(self):
        today = datetime.date.today()
        return self.filter(
            Q(begin_date__lte=today, end_date__isnull=True) |
            Q(begin_date__isnull=True, end_date__gte=today) |
            Q(begin_date__lte=today, end_date__gte=today) |
            Q(begin_date__isnull=True, end_date__isnull=True))
