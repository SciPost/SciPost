__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class PublicationExpenditureCoverage(models.Model):
    """
    An amount from a Subsidy which is ascribed to a Publication as expenditure coverage.

    A Coverage is applied to a Publication as a whole, not to individual PubFracs.
    This class thus complements PubFracCompensation, which compensates costs
    at the PubFrac level.
    """

    subsidy = models.ForeignKey(
        "finances.Subsidy",
        related_name="pex_coverages",
        on_delete=models.CASCADE,
    )

    publication = models.ForeignKey(
        "journals.Publication",
        related_name="pex_coverages",
        on_delete=models.CASCADE,
    )

    amount = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subsidy", "publication"], name="unique_subsidy_publication"
            ),
        ]
        verbose_name = "PEX coverage"
        verbose_name_plural = "PEX coverages"

    def __str__(self):
        return (
            f"€{self.amount} for {self.publication.doi_label} "
            "from {self.subsidy.organization}"
        )
