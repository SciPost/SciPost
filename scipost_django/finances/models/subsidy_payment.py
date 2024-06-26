__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from ..managers import SubsidyPaymentQuerySet


class SubsidyPayment(models.Model):
    subsidy = models.ForeignKey(
        "finances.Subsidy",
        related_name="payments",
        on_delete=models.CASCADE,
    )
    reference = models.CharField(max_length=64, unique=True)
    amount = models.PositiveIntegerField(help_text="in &euro;")
    date_scheduled = models.DateField()
    invoice = models.OneToOneField(
        "finances.SubsidyAttachment",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="invoice_for",
    )
    proof_of_payment = models.OneToOneField(
        "finances.SubsidyAttachment",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="proof_of_payment_for",
    )

    objects = SubsidyPaymentQuerySet.as_manager()

    class Meta:
        ordering = ["date_scheduled", "reference", "amount"]

    def __str__(self):
        return f"payment {self.reference} for {self.subsidy}"

    @property
    def status(self):
        if self.paid:
            return "paid"
        if self.invoiced:
            return "invoiced"
        return "scheduled"

    @property
    def invoiced(self):
        return self.invoice is not None

    @property
    def invoice_date(self):
        return self.invoice.date if self.invoice else None

    @property
    def paid(self):
        return self.proof_of_payment is not None

    @property
    def payment_date(self):
        return self.proof_of_payment.date if self.proof_of_payment else None
