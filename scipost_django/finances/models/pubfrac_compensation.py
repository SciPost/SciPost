__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class PubFracCompensation(models.Model):
    """
    An amount from a Subsidy which ascribed to a PubFrac as compensation.
    """

    subsidy = models.ForeignKey(
        "finances.Subsidy",
        related_name="pubfrac_compensations",
        on_delete=models.CASCADE,
    )

    pubfrac = models.ForeignKey(
        "finances.PubFrac",
        related_name="pubfracs",
        on_delete=models.CASCADE,
    )

    amount = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subsidy", "pubfrac"], name="unique_subsidy_pubfrac"
            ),
        ]
        verbose_name_plural = "PubFrac Compensations"
