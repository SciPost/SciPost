import datetime

from django.db import models
from django.db.models import Q


class FellowQuerySet(models.QuerySet):
    def guests(self):
        return self.filter(guest=True)

    def regular(self):
        return self.filter(guest=False)

    def active(self):
        today = datetime.date.today()
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True)
            ).order_by('contributor__user__last_name')
