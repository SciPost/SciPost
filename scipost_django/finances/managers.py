__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED


class SubsidyQuerySet(models.QuerySet):
    def obtained(self):
        return self.filter(
            status__in=[SUBSIDY_PROMISED, SUBSIDY_INVOICED, SUBSIDY_RECEIVED],
        )


class SubsidyAttachmentQuerySet(models.QuerySet):

    def agreements(self):
        return self.filter(kind=self.model.KIND_AGREEMENT)

    def proofs_of_payment(self):
        return self.filter(kind=self.model.KIND_PROOF_OF_PAYMENT)
