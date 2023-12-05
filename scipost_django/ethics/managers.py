__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone


class CompetingInterestQuerySet(models.QuerySet):
    def valid_on_date(self, date: datetime.date = None):
        """
        Filter for validity on given optional date.
        """
        if not date:
            date = timezone.now().date()
        return self.filter(
            Q(date_from__lte=date, date_until__isnull=True)
            | Q(date_from__isnull=True, date_until__gte=date)
            | Q(date_from__lte=date, date_until__gte=date)
            | Q(date_from__isnull=True, date_until__isnull=True)
        ).order_by()

    def involving_profile(self, profile):
        """
        Filter for CompetingInterests involving given Profile.
        """
        return self.filter(Q(profile=profile) | Q(related_profile=profile))
