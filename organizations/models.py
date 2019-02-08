__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse

from django_countries.fields import CountryField

from .constants import ORGANIZATION_TYPES, ORGTYPE_PRIVATE_BENEFACTOR,\
    ORGANIZATION_STATUSES, ORGSTATUS_ACTIVE
from .managers import OrganizationQuerySet

from scipost.models import Contributor
from journals.models import Publication, OrgPubFraction, UnregisteredAuthor


class Organization(models.Model):
    """
    An Organization instance is any type of administrative unit which SciPost
    can interact with. Example types include universities, funding agencies,
    research institutes etc.

    All instances can only be created by SciPost administration-level personnel,
    and can thus be considered as verified.

    These objects are meant to be internally linked to all other types of
    (possibly user-defined) objects used throughout the site (such as Institutions,
    Partners, Affiliations, Funders etc). This enables relating all of SciPost's
    services to the organizations which are impacted by its activities.

    The data here is also meant to be cross-linked to external databases,
    for example the Global Research Identifier Database (GRID), Crossref,
    ORCID etc.
    """
    orgtype = models.CharField(max_length=32, choices=ORGANIZATION_TYPES)
    status = models.CharField(max_length=32, choices=ORGANIZATION_STATUSES,
                              default=ORGSTATUS_ACTIVE)
    name = models.CharField(max_length=256,
                            help_text="Western version of name")
    name_original = models.CharField(max_length=256, blank=True,
                                     help_text="Name (in original language)")
    acronym = models.CharField(max_length=64, blank=True,
                               help_text='Acronym or short name')
    country = CountryField()
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True)
    css_class = models.CharField(max_length=256, blank=True,
                                 verbose_name="Additional logo CSS class")
    grid_json = JSONField(default={}, blank=True, null=True) # JSON data from GRID
    crossref_json = JSONField(default={}, blank=True, null=True) # JSON data from Crossref
    parent = models.ForeignKey('self', blank=True, null=True,
                               on_delete=models.SET_NULL, related_name='children')
    superseded_by = models.ForeignKey('self', blank=True, null=True,
                                         on_delete=models.SET_NULL)
    # Calculated fields (to save CPU; field name always starts with cf_)
    # Number of associated publications; needs to be updated when any related
    # affiliation, grant or f
    cf_nr_associated_publications = models.PositiveIntegerField(
        blank=True, null=True,
        help_text='NB: nr_associated_publications is a calculated field. Do not modify.')

    objects = OrganizationQuerySet.as_manager()

    class Meta:
        ordering = ['country', 'name']

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        full_name_str = ""
        if self.name_original:
            full_name_str += "%s / " % self.name_original
        full_name_str += "%s" % self.name
        return full_name_str

    @property
    def full_name_with_acronym(self):
        full_name_str = self.full_name
        if self.acronym:
            full_name_str += " [%s]" % self.acronym
        return full_name_str

    def get_absolute_url(self):
        return reverse('organizations:organization_details', kwargs = {'pk': self.id})

    @property
    def details_publicly_viewable(self):
        return self.orgtype != ORGTYPE_PRIVATE_BENEFACTOR

    def get_publications(self):
        org_and_children_ids = [k['id'] for k in list(self.children.all().values('id'))]
        org_and_children_ids += [self.id]
        return Publication.objects.filter(
            models.Q(authors__affiliations__pk__in=org_and_children_ids) |
            models.Q(grants__funder__organization__pk__in=org_and_children_ids) |
            models.Q(funders_generic__organization__pk__in=org_and_children_ids)).distinct()

    def count_publications(self):
        return self.get_publications().count()

    def update_cf_nr_associated_publications(self):
        """
        Update the calculated field Organization:cf_nr_associated_publications.
        """
        self.cf_nr_associated_publications = self.count_publications()
        self.save()

    def pubfraction_for_publication(self, doi_label):
        """
        Return the organization's pubfraction for this publication, or the string 'Not defined'.
        """
        try:
            return OrgPubFraction.objects.get(
                organization=self,
                publication__doi_label=doi_label).fraction
        except:
            return 'Not yet defined'

    def pubfractions_in_year(self, year):
        """
        Returns the sum of pubfractions for the given year.
        """
        return OrgPubFraction.objects.filter(
            organization=self,
            publication__publication_date__year=year
        ).aggregate(Sum('fraction'))['fraction__sum']

    def get_contributor_authors(self):
        cont_id_list = [tbl.contributor.id for tbl in self.publicationauthorstable_set.all() \
                     if tbl.contributor is not None]
        return Contributor.objects.filter(id__in=cont_id_list).order_by('user__last_name')

    def get_unregistered_authors(self):
        unreg_id_list = [tbl.unregistered_author.id for tbl in self.publicationauthorstable_set.all(
        ) if tbl.unregistered_author is not None]
        return UnregisteredAuthor.objects.filter(id__in=unreg_id_list).order_by('last_name')

    @property
    def has_current_agreement(self):
        """
        Check if this organization has a current Partnership agreement.
        """
        if not self.partner:
            return False
        return self.partner.agreements.now_active().exists()

    @property
    def has_current_subsidy(self):
        """
        Check if this organization has a Subsidy with a still-running validity period.
        """
        return self.subsidy_set.filter(date_until__gte=datetime.date.today()).exists()

    def get_total_subsidies_obtained(self, n_years_past=None):
        """
        Computes the total amount received by SciPost, in the form
        of subsidies from this Organization.
        """
        return self.subsidy_set.aggregate(models.Sum('amount')).get('amount__sum', 0)

    def get_total_contribution_obtained(self, n_years_past=None):
        """
        Computes the contribution obtained from this organization,
        summed over all time.
        """
        contrib = 0
        for agreement in self.partner.agreements.all():
            contrib += agreement.offered_yearly_contribution * int(agreement.duration.days / 365)
        return contrib
