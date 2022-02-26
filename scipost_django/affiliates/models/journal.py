__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import validate_unicode_slug
from django.db import models
from django.urls import reverse


def cost_default_value():
    return {"default": 400}


class AffiliateJournal(models.Model):
    """
    A Journal which piggybacks on SciPost's services.
    """

    publisher = models.ForeignKey(
        "affiliates.AffiliatePublisher",
        on_delete=models.CASCADE,
        related_name="journals",
    )

    name = models.CharField(max_length=256)

    short_name = models.CharField(max_length=256, default="")

    slug = models.SlugField(
        max_length=128,
        validators=[
            validate_unicode_slug,
        ],
        unique=True,
    )

    homepage = models.URLField(max_length=256, blank=True)

    # Cost per publication information
    cost_info = models.JSONField(default=cost_default_value)

    class Meta:
        ordering = ["publisher", "name"]
        permissions = (("manage_journal_content", "Manage Journal content"),)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("affiliates:journal_detail", kwargs={"slug": self.slug})
