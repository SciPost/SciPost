__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import validate_unicode_slug
from django.db import models
from django.urls import reverse


class AffiliateJournal(models.Model):
    """
    A Journal which piggybacks on SciPost's services.
    """

    publisher = models.ForeignKey(
        'affiliates.AffiliatePublisher',
        on_delete=models.CASCADE,
        related_name='journals'
    )

    name = models.CharField(
        max_length=256
    )

    # Note that the short name can be just as long as the full name. This is because not all
    # journals have abbreviated names in Crossref, and instead return the full journal name.
    short_name = models.CharField(
        max_length=256,
        default=""
    )

    slug = models.SlugField(
        max_length=128,
        validators=[validate_unicode_slug,],
        unique=True
    )

    class Meta:
        ordering = [
            'publisher',
            'name'
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'affiliates:journal_detail',
            kwargs={'slug': self.slug}
        )
