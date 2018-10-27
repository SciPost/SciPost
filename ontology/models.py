__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class Tag(models.Model):
    """
    Tags can be attached to a Topic to specify which category it fits.
    Examples: Concept, Device, Model, Theory, ...
    """
    name = models.CharField(max_length=32, unique=True)

    class Meta:
        ordering = ['name']


class Topic(models.Model):
    """
    A Topic represents one of the nodes in the ontology.
    """
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.name
