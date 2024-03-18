__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from decimal import Decimal

from django.db import models

from ..managers import PubFracQuerySet


class PubFrac(models.Model):
    """
    A fraction of a given Publication related to an Organization.

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
    compensated_by = models.ForeignKey(
        "finances.Subsidy",
        related_name="compensated_pubfracs",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    # Calculated field
    cf_value = models.DecimalField(
        max_digits=16, decimal_places=3, blank=True, null=True
    )

    objects = PubFracQuerySet.as_manager()

    class Meta:
        unique_together = (("organization", "publication"),)
        verbose_name = "PubFrac"
        verbose_name_plural = "PubFracs"

    def __str__(self):
        return (
            f"{str(self.fraction)} (€{int(self.cf_value)}) "
            f"for {self.publication.doi_label} from {self.organization}"
        )

    def save(self, *args, **kwargs):
        self.cf_value = self.fraction * self.publication.expenditures
        return super().save(*args, **kwargs)

    @property
    def compensated(self):
        return self.compensated_by is not None
