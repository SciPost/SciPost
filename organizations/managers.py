__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models


class OrganizationQuerySet(models.QuerySet):

    def current_sponsors(self):
        return self.filter(subsidy__date_until__gte=datetime.date.today())

    def with_subsidy_above_and_up_to(self, min_amount, max_amount=None):
        """
        List of sponsors with at least one subsidy above parameter:amount.
        """
        qs = self.annotate(max_subsidy=models.Max('subsidy__amount')
        ).filter(max_subsidy__gte=min_amount)
        if max_amount:
            qs = qs.filter(max_subsidy__lt=max_amount)
        return qs
