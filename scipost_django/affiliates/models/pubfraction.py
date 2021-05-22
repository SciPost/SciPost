__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from decimal import Decimal

from django.db import models


class AffiliatePubFraction(models.Model):
    """
    PubFraction for an AffiliatePublication.
    """
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='affiliate_pubfractions'
    )
    publication = models.ForeignKey(
        'affiliates.AffiliatePublication',
        on_delete=models.CASCADE,
        related_name='pubfractions'
    )
    fraction = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=Decimal('0.000')
    )

    class Meta:
        unique_together = (
            ('organization', 'publication'),
        )

    def __str__(self):
        return 'PubFraction of %s for %s: %s' % (
            self.organization,
            self.publication,
            self.fraction
        )
