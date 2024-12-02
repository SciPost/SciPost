__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import SUBSIDY_WITHDRAWN, SUBSIDY_TYPE_INDIVIDUAL_BUDGET


class SubsidyQuerySet(models.QuerySet):
    def obtained(self):
        return self.exclude(status=SUBSIDY_WITHDRAWN)

    def direct(self):
        return self.exclude(subsidy_type=SUBSIDY_TYPE_INDIVIDUAL_BUDGET)

    def through_individual_budget(self):
        return self.filter(subsidy_type=SUBSIDY_TYPE_INDIVIDUAL_BUDGET)


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


class PubFracQuerySet(models.QuerySet):
    def uncompensated(self):
        return self.filter(compensated_by__isnull=True)

    def compensated(self):
        return self.exclude(compensated_by__isnull=True)
