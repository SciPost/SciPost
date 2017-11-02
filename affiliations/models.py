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
    country = CountryField()
    type = models.CharField(max_length=16, choices=INSTITUTE_TYPES, default=TYPE_UNIVERSITY)

    class Meta:
        default_related_name = 'institutes'
        ordering = ['country']

    def __str__(self):
        return '{name} ({country})'.format(name=self.name, country=self.get_country_display())

    def get_absolute_url(self):
        return reverse('affiliations:institute_details', args=(self.id,))


class Affiliation(models.Model):
    """
    An Affiliation is a (time dependent) connection between an Institute and a Contributor.
    This could thus be changed over time and history will be preserved.
    """
    institute = models.ForeignKey('affiliations.Institute')
    contributor = models.ForeignKey('scipost.Contributor')
    begin_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        default_related_name = 'affiliations'

    def __str__(self):
        return '{contributor} ({institute})'.format(
            contributor=self.contributor, institute=self.institute.name)
