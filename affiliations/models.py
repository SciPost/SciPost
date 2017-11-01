from django.db import models

from django_countries.fields import CountryField

from .constants import AFFILIATION_TYPES, AFFILIATION_UNIVERSITY


class Affiliation(models.Model):
    """
    Any Scientific affiliation in the world should ideally have a SciPost registration.
    """
    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=16, blank=True)
    # address = models.TextField(blank=True)
    country = CountryField()
    type = models.CharField(max_length=16, choices=AFFILIATION_TYPES,
                            default=AFFILIATION_UNIVERSITY)

    def __str__(self):
        return self.name
