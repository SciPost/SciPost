import datetime

from django.db import models
from django.db.models import Q


class FellowManager(models.Manager):
    def active(self, *args, **kwargs):
        today = datetime.date.today()
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True) |
            Q(start_date__isnull=True, until_date__gte=today) |
            Q(start_date__lte=today, until_date__gte=today) |
            Q(start_date__isnull=True, until_date__isnull=True),
            **kwargs).order_by('contributor__user__last_name')
