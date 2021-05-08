__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse

from ..validators import doi_affiliatepublication_validator


class AffiliatePublication(models.Model):
    """
    Publication item from an affiliate Publisher/Journal.
    """

    doi = models.CharField(
        max_length=256,
        unique=True,
        db_index=True,
        validators=[doi_affiliatepublication_validator]
    )
    _metadata_crossref = JSONField(
        default=dict,
        blank=True
    )

    journal = models.ForeignKey(
        'affiliates.AffiliateJournal',
        on_delete=models.CASCADE,
        related_name='publications'
    )

    def __str__(self):
        return self.doi

    def get_absolute_url(self):
        return reverse(
            'affiliates:publication_detail',
            kwargs={'doi': self.doi}
        )
