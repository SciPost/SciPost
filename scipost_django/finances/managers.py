__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from .constants import SUBSIDY_WITHDRAWN, SUBSIDY_TYPE_INDIVIDUAL_BUDGET

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from finances.models.pubfrac import PubFrac


class SubsidyQuerySet(models.QuerySet):
    def obtained(self):
        return self.exclude(status=SUBSIDY_WITHDRAWN)

    def direct(self):
        return self.exclude(subsidy_type=SUBSIDY_TYPE_INDIVIDUAL_BUDGET)

    def through_individual_budget(self):
        return self.filter(subsidy_type=SUBSIDY_TYPE_INDIVIDUAL_BUDGET)

    def sequentially_renewable(self):
        """
        Returns subsidies that are eligible to be renewed without the breaking of a
        sponsorship period, i.e. those that can be renewed and whose end date elapsed
        no more than one year ago (current, and last year ones).
        For a sponsorship within a calendar year, the sponsor is named "current" during that year
        and marked as "pending renewal" for the next year.
        Sponsors not renewing for more than one year are then considered "past".
        """
        return self.filter(renewable=True).exclude(
            models.Q(date_until__year__lt=timezone.now().year - 1)
        )


class SubsidyPaymentQuerySet(models.QuerySet):
    def outstanding(self):
        return self.filter(proof_of_payment__isnull=True)

    def paid(self):
        return self.filter(proof_of_payment__isnull=False)


class SubsidyAttachmentQuerySet(models.QuerySet):
    def agreements(self):
        return self.filter(kind=self.model.KIND_AGREEMENT)

    def invoices(self):
        return self.filter(kind=self.model.KIND_INVOICE)

    def proofs_of_payment(self):
        return self.filter(kind=self.model.KIND_PROOF_OF_PAYMENT)

    def orphaned(self):
        return self.filter(subsidy__isnull=True).order_by("date")

    def unattached(self):
        return self.filter(
            models.Q(proof_of_payment_for__isnull=True)
            & models.Q(invoice_for__isnull=True)
        )


class PubFracQuerySet(models.QuerySet["PubFrac"]):
    def uncompensated(self):
        return self.filter(compensated_by__isnull=True)

    def compensated(self):
        return self.exclude(compensated_by__isnull=True)

    def duplicate_of(self, pubfrac: "PubFrac") -> "PubFrac | None":
        """
        Returns a duplicate PubFrac instance if it exists, None otherwise.
        """
        return (
            self.filter(
                organization=pubfrac.organization,
                publication=pubfrac.publication,
            )
            .exclude(pk=pubfrac.pk)
            .first()
        )
