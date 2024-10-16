__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db import models


class Balance(models.Model):

    account = models.ForeignKey(
        "Account", on_delete=models.CASCADE, related_name="balance_entries"
    )
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["account", "date"], name="unique_balance")
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.account} at EUR {self.amount} on {self.date}"
