__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models

from finances.constants import SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED


class OrganizationQuerySet(models.QuerySet):
    def all_sponsors(self):
        """
        All Organizations which have subsidized SciPost at least once in the past.
        """
        return self.filter(
            subsidy__status__in=[SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED],
            subsidy__amount__gte=0,
        )

    def current_sponsors(self):
        """
        Organizations which have a Subsidy which is ongoing (date_until <= today).
        """
        return self.filter(
            subsidy__status__in=[SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED],
            subsidy__date_until__gte=datetime.date.today(),
        )

    def with_subsidy_above_and_up_to(self, min_amount, max_amount=None):
        """
        List of sponsors with at least one subsidy above parameter:amount.
        """
        qs = self.filter(
            subsidy__status__in=[SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED],
        ).annotate(max_subsidy=models.Max("subsidy__amount")).filter(
            max_subsidy__gte=min_amount
        )
        if max_amount:
            qs = qs.filter(max_subsidy__lt=max_amount)
        return qs

    def order_by_total_amount_received(self):
        """
        Order by (decreasing) total amount received.
        """
        return self.filter(
            subsidy__status__in=[SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED],
        ).annotate(total=models.Sum("subsidy__amount")).order_by("-total")
