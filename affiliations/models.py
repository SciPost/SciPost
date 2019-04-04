__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse

from django_countries.fields import CountryField

from scipost.models import Contributor

from .constants import INSTITUTION_TYPES, TYPE_UNIVERSITY
from .managers import AffiliationQuerySet


class Institution(models.Model):
    """
    Any (scientific) Institution with a SciPost registration.
    """

    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=16, blank=True)
    country = CountryField()
    type = models.CharField(max_length=16, choices=INSTITUTION_TYPES, default=TYPE_UNIVERSITY)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE,
                                     blank=True, null=True)

    class Meta:
        default_related_name = 'institutions'
        ordering = ['country']

    def __str__(self):
        return '{name} ({country})'.format(name=self.name, country=self.get_country_display())

    def get_absolute_url(self):
        """Return the Institution detail page."""
        return reverse('affiliations:institution_details', args=(self.id,))

    def contributors(self):
        """All Contributor instances related to the Institution."""
        return Contributor.objects.filter(affiliations__institution=self)


class Affiliation(models.Model):
    """
    An Affiliation is a (time dependent) connection between an Institution and a Contributor.
    This could thus be changed over time and history will be preserved.
    """
    institution = models.ForeignKey('affiliations.Institution')
    contributor = models.ForeignKey('scipost.Contributor')
    begin_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    objects = AffiliationQuerySet.as_manager()

    class Meta:
        default_related_name = 'affiliations'
        ordering = ['begin_date', 'end_date', 'institution']

    def __str__(self):
        return '{contributor} ({institution})'.format(
            contributor=self.contributor, institution=self.institution.name)
