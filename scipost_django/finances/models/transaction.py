__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db import models

from finances.models import Account


class Transaction(models.Model):

    account = models.ForeignKey[Account](Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField()

    class Meta:
        ordering = ["-datetime"]
        default_related_name = "transactions"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "datetime"], name="unique_transaction"
            )
        ]


class FuturePeriodicTransaction(models.Model):
    """
    Represents a future transaction (expense or income) that we expect to happen
    in the future at some frequency. This is used to predict future balances.
    """

    account = models.ForeignKey[Account](Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_from = models.DateField()
    period = models.DurationField()
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_from"]
        default_related_name = "future_transactions"
