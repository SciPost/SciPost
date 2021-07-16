__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

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
    _metadata_crossref = models.JSONField(
        default=dict,
        blank=True
    )
    journal = models.ForeignKey(
        'affiliates.AffiliateJournal',
        on_delete=models.CASCADE,
        related_name='publications'
    )
    publication_date = models.DateField(
        blank=True, null=True
    )

    class Meta:
        ordering = [
            '-publication_date',
        ]

    def __str__(self):
        return self.doi

    def get_absolute_url(self):
        return reverse(
            'affiliates:publication_detail',
            kwargs={'doi': self.doi}
        )

    def get_title(self):
        return self._metadata_crossref.get('title', [])[0]

    def get_author_list(self):
        """Comma-separated list of authors first name last name."""
        author_list = []
        for author in self._metadata_crossref.get('author', []):
            try:
                author_list.append('{} {}'.format(author['given'], author['family']))
            except KeyError:
                author_list.append(author['name'])
        author_list = ', '.join(author_list)
        return author_list

    def get_volume(self):
        return self._metadata_crossref.get('volume', '')

    def get_pages(self):
        pages = self._metadata_crossref.get('article-number', '')
        if not pages:
            pages = self._metadata_crossref.get('page', '')
        return pages

    def get_sum_pubfractions(self):
        sum = 0
        for pubfrac in self.pubfractions.all():
            sum += pubfrac.fraction
        return sum
