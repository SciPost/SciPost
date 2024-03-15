__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from decimal import Decimal

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


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

    # Calculated field
    cf_value = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = (("organization", "publication"),)
        verbose_name = "PubFrac"
        verbose_name_plural = "PubFracs"

    def __str__(self):
        return (f"{str(self.fraction)} (€{self.cf_value}) "
                f"for {self.publication.doi_label} from {self.organization}")


@receiver(pre_save, sender=PubFrac)
def calculate_cf_value(sender, instance: PubFrac, **kwargs):
    """Calculate the cf_value field before saving."""
    instance.cf_value = int(
        instance.fraction * instance.publication.get_journal(
        ).cost_per_publication(
            instance.publication.publication_date.year
        )
    )
