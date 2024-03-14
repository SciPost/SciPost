__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from decimal import Decimal

from django.db import models


class PubFrac(models.Model):
    """
    A fraction of a given Publication related to an Organization, for expenditure redistribution.

    Fractions for a given Publication should sum up to one.

    This data is used to compile publicly-displayed information on Organizations
    as well as to set suggested contributions from sponsoring Organizations.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="pubfracs",
        blank=True,
        null=True,
    )
    publication = models.ForeignKey(
        "journals.Publication", on_delete=models.CASCADE, related_name="pubfracs"
    )
    fraction = models.DecimalField(
        max_digits=4, decimal_places=3, default=Decimal("0.000")
    )

    class Meta:
        unique_together = (("organization", "publication"),)

    @property
    def value(self):
        return int(self.fraction * self.publication.get_journal().cost_per_publication(
            self.publication.publication_date.year
        ))
