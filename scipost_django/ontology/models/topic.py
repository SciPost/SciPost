__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse


class Topic(models.Model):
    """
    A Topic represents one of the nodes in the ontology.
    """

    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    tags = models.ManyToManyField("ontology.Tag", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_abolute_url(self):
        return reverse("ontology:topic_details", kwargs={"slug": self.slug})
