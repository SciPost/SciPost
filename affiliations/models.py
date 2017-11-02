from django.db import models
from django.urls import reverse

from django_countries.fields import CountryField

from .constants import INSTITUTE_TYPES, TYPE_UNIVERSITY


class Institute(models.Model):
    """
    Any (scientific) Institute in the world should ideally have a SciPost registration.
    """
    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=16, blank=True)
    # address = models.TextField(blank=True)
    country = CountryField()
    type = models.CharField(max_length=16, choices=INSTITUTE_TYPES, default=TYPE_UNIVERSITY)

    class Meta:
        default_related_name = 'affiliations'
        ordering = ['country']

    def __str__(self):
        return '{name} ({country})'.format(name=self.name, country=self.get_country_display())

    def get_absolute_url(self):
        return reverse('affiliations:affiliation_details', args=(self.id,))
