__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import SUBSIDY_WITHDRAWN


class SubsidyQuerySet(models.QuerySet):
    def obtained(self):
        return self.exclude(status=SUBSIDY_WITHDRAWN)


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
