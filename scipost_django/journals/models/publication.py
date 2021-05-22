__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from decimal import Decimal

from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Min, Sum
from django.urls import reverse

from ..constants import (STATUS_DRAFT, STATUS_PUBLISHED,
    PUBLICATION_PUBLISHED, CCBY4, CC_LICENSES, CC_LICENSES_URI, PUBLICATION_STATUSES)
from ..helpers import paper_nr_string
from ..managers import PublicationQuerySet
from ..validators import doi_publication_validator

from scipost.constants import SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField


class PublicationAuthorsTable(models.Model):
    """
    PublicationAuthorsTable represents an author of a Publication.

    Fields:

    * publication
    * profile
    * affiliations: for this author/Publication (supersede profile.affiliations)
    * order: the ordinal position of this author in this Publication's list of authors.
    """

    publication = models.ForeignKey('journals.Publication', on_delete=models.CASCADE,
                                    related_name='authors')
    profile = models.ForeignKey('profiles.Profile', on_delete=models.PROTECT,
                                blank=True, null=True)
    affiliations = models.ManyToManyField('organizations.Organization', blank=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return str(self.profile)

    def save(self, *args, **kwargs):
        """Auto increment order number if not explicitly set."""
        if not self.order:
            self.order = self.publication.authors.count() + 1
        return super().save(*args, **kwargs)

    @property
    def is_registered(self):
        """Check if author is registered at SciPost."""
        return self.profile.contributor is not None

    @property
    def first_name(self):
        """Return first name of author."""
        return self.profile.first_name

    @property
    def last_name(self):
        """Return last name of author."""
        return self.profile.last_name



class Publication(models.Model):
    """A Publication is an object directly related to an accepted Submission.

    It contains metadata, the actual publication file, author data, etc. etc.
    It may be directly related to a Journal or to an Issue.
    """

    # Publication data
    accepted_submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE,
                                               related_name='publication')
    in_issue = models.ForeignKey(
        'journals.Issue', on_delete=models.CASCADE, null=True, blank=True,
        help_text='Assign either an Issue or Journal to the Publication')
    in_journal = models.ForeignKey(
        'journals.Journal', on_delete=models.CASCADE, null=True, blank=True,
        help_text='Assign either an Issue or Journal to the Publication')
    paper_nr = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=8,
                              choices=PUBLICATION_STATUSES, default=STATUS_DRAFT)

    # Core fields
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=10000, verbose_name="author list")
    abstract = models.TextField()
    abstract_jats = models.TextField(blank=True, default='',
                                     help_text='JATS version of abstract for Crossref deposit')
    pdf_file = models.FileField(upload_to='UPLOADS/PUBLICATIONS/%Y/%m/', max_length=200)

    # Ontology-based semantic linking
    acad_field = models.ForeignKey(
        'ontology.AcademicField',
        on_delete=models.PROTECT,
        related_name='publications'
    )
    specialties = models.ManyToManyField(
        'ontology.Specialty',
        related_name='publications'
    )
    topics = models.ManyToManyField(
        'ontology.Topic',
        blank=True
    )
    approaches = ChoiceArrayField(
        models.CharField(max_length=24, choices=SCIPOST_APPROACHES),
        blank=True, null=True, verbose_name='approach(es) [optional]')

    cc_license = models.CharField(max_length=32, choices=CC_LICENSES, default=CCBY4)

    # Funders
    grants = models.ManyToManyField('funders.Grant', blank=True)
    funders_generic = models.ManyToManyField('funders.Funder', blank=True)  # not linked to a grant
    pubfractions_confirmed_by_authors = models.BooleanField(default=False)

    # Metadata
    metadata = JSONField(default=dict, blank=True, null=True)
    metadata_xml = models.TextField(blank=True)  # for Crossref deposit
    metadata_DOAJ = JSONField(default=dict, blank=True, null=True)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_publication_validator])
    BiBTeX_entry = models.TextField(blank=True)
    doideposit_needs_updating = models.BooleanField(default=False)
    citedby = JSONField(default=dict, blank=True, null=True)
    number_of_citations = models.PositiveIntegerField(default=0)

    # Date fields
    submission_date = models.DateField(verbose_name='submission date')
    acceptance_date = models.DateField(verbose_name='acceptance date')
    publication_date = models.DateField(verbose_name='publication date')
    latest_citedby_update = models.DateTimeField(null=True, blank=True)
    latest_metadata_update = models.DateTimeField(blank=True, null=True)
    latest_activity = models.DateTimeField(auto_now=True)  # Needs `auto_now` as its not explicity updated anywhere?

    # Calculated fields
    cf_author_affiliation_indices_list = ArrayField(
        ArrayField(
            models.PositiveSmallIntegerField(blank=True, null=True),
            default=list
        ),
        default=list
    )

    objects = PublicationQuerySet.as_manager()

    class Meta:
        default_related_name = 'publications'
        ordering = ('-publication_date', '-paper_nr')

    def __str__(self):
        return '{cite}, {title} by {authors}, {date}'.format(
            cite=self.citation,
            title=self.title[:30],
            authors=self.author_list[:30],
            date=self.publication_date.strftime('%Y-%m-%d'))

    def clean(self):
        """Check if either a valid Journal or Issue is assigned to the Publication."""
        if not (self.in_journal or self.in_issue):
            raise ValidationError({
                'in_journal': ValidationError(
                    'Either assign a Journal or Issue to this Publication', code='required'),
                'in_issue': ValidationError(
                    'Either assign a Journal or Issue to this Publication', code='required'),
            })
        if self.in_journal and self.in_issue:
            # Assigning both a Journal and an Issue will screw up the database
            raise ValidationError({
                'in_journal': ValidationError(
                    'Either assign only a Journal or Issue to this Publication', code='invalid'),
                'in_issue': ValidationError(
                    'Either assign only a Journal or Issue to this Publication', code='invalid'),
            })
        if self.in_issue and not self.get_journal().has_issues:
            # Assigning both a Journal and an Issue will screw up the database
            raise ValidationError({
                'in_issue': ValidationError(
                    'This journal does not allow the use of Issues',
                    code='invalid'),
            })
        if self.in_journal and self.get_journal().has_issues:
            # Assigning both a Journal and an Issue will screw up the database
            raise ValidationError({
                'in_journal': ValidationError(
                    'This journal does not allow the use of individual Publications',
                    code='invalid'),
            })

    def get_absolute_url(self):
        return reverse('scipost:publication_detail', args=(self.doi_label,))

    def get_cc_license_URI(self):
        for (key, val) in CC_LICENSES_URI:
            if key == self.cc_license:
                return val
        raise KeyError

    def get_all_affiliations(self):
        """
        Returns all author affiliations.
        """
        from organizations.models import Organization
        return Organization.objects.filter(
            publicationauthorstable__publication=self
        ).annotate(order=Min('publicationauthorstable__order')).order_by('order')

    def get_author_affiliation_indices_list(self):
        """
        Return a list containing for each author an ordered list of affiliation indices.

        This is for display on the publication detail page,
        and is a calculated field (saved in the model) to avoid
        unnecessary db queries (problematic for papers with large number of authors).
        """
        if len(self.cf_author_affiliation_indices_list) > 0:
            return self.cf_author_affiliation_indices_list

        indexed_author_list = []
        for author in self.authors.all():
            affnrs = []
            for idx, aff in enumerate(self.get_all_affiliations()):
                if aff in author.affiliations.all():
                    affnrs.append(idx + 1)
            indexed_author_list.append(affnrs)
        # Since nested ArrayFields must have the same dimension,
        # we pad the "empty" entries with Null:
        max_length = 0
        for entry in indexed_author_list:
            max_length = max(max_length, len(entry))
        padded_list = []
        for entry in indexed_author_list:
            padded_entry = entry + [None] * (max_length - len(entry))
            padded_list.append(padded_entry)
        # Save into the calculated field for future purposes.
        Publication.objects.filter(id=self.id).update(
            cf_author_affiliation_indices_list=padded_list)
        return padded_list

    def get_all_funders(self):
        from funders.models import Funder
        return Funder.objects.filter(
            models.Q(grants__publications=self) | models.Q(publications=self)).distinct()

    def get_organizations(self):
        """
        Returns a queryset of all Organizations which are associated to this Publication,
        through being in author affiliations, funders or generic funders.
        """
        from organizations.models import Organization
        return Organization.objects.filter(
            models.Q(publicationauthorstable__publication=self) |
            models.Q(funder__grants__publications=self) |
            models.Q(funder__publications=self)).distinct()

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    @property
    def is_draft(self):
        return self.status == STATUS_DRAFT

    @property
    def is_published(self):
        if self.status != PUBLICATION_PUBLISHED:
            return False

        if self.in_issue:
            return self.in_issue.status == STATUS_PUBLISHED
        elif self.in_journal:
            return self.in_journal.active
        return False

    @property
    def has_xml_metadata(self):
        return self.metadata_xml != ''

    @property
    def has_bibtex_entry(self):
        return self.BiBTeX_entry != ''

    @property
    def has_citation_list(self):
        return 'citation_list' in self.metadata and len(self.metadata['citation_list']) > 0

    @property
    def has_funding_statement(self):
        return 'funding_statement' in self.metadata and self.metadata['funding_statement']

    @property
    def pubfractions_sum_to_1(self):
        """ Checks that the support fractions sum up to one. """
        return self.pubfractions.aggregate(Sum('fraction'))['fraction__sum'] == 1

    @property
    def citation(self):
        """Return Publication name in the preferred citation format."""
        if self.in_issue and self.in_issue.in_volume:
            return '{journal} {volume}, {paper_nr} ({year})'.format(
                journal=self.in_issue.in_volume.in_journal.name_abbrev,
                volume=self.in_issue.in_volume.number,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime('%Y'))
        elif self.in_issue and self.in_issue.in_journal:
            return '{journal} {issue}, {paper_nr} ({year})'.format(
                journal=self.in_issue.in_journal.name_abbrev,
                issue=self.in_issue.number,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime('%Y'))
        elif self.in_journal:
            return '{journal} {paper_nr} ({year})'.format(
                journal=self.in_journal.name_abbrev,
                paper_nr=self.paper_nr,
                year=self.publication_date.strftime('%Y'))
        return '{paper_nr} ({year})'.format(
            paper_nr=self.paper_nr,
            year=self.publication_date.strftime('%Y'))

    def get_cc_license_URI(self):
        for (key, val) in CC_LICENSES_URI:
            if key == self.cc_license:
                return val
        raise KeyError

    def get_all_funders(self):
        from funders.models import Funder
        return Funder.objects.filter(
            models.Q(grants__publications=self) | models.Q(publications=self)).distinct()

    def get_journal(self):
        if self.in_journal:
            return self.in_journal
        elif self.in_issue.in_journal:
            return self.in_issue.in_journal
        return self.in_issue.in_volume.in_journal

    def journal_issn(self):
        return self.get_journal().issn

    def get_paper_nr(self):
        if self.in_journal:
            return self.paper_nr
        return paper_nr_string(self.paper_nr)

    def citation_rate(self):
        """Returns the citation rate in units of nr citations per article per year."""
        if self.citedby and self.latest_citedby_update:
            ncites = len(self.citedby)
            deltat = (self.latest_citedby_update.date() - self.publication_date).days
            return (ncites * 365.25 / deltat)
        else:
            return 0

    def get_issue_related_publications(self):
        """Return 4 Publications within same Issue."""
        return Publication.objects.published().filter(
            in_issue=self.in_issue).exclude(id=self.id)[:4]


class Reference(models.Model):
    """A Refence is a reference used in a specific Publication."""
    reference_number = models.IntegerField()
    publication = models.ForeignKey('journals.Publication', on_delete=models.CASCADE)

    authors = models.CharField(max_length=1028)
    citation = models.CharField(max_length=1028, blank=True)
    identifier = models.CharField(blank=True, max_length=128)
    link = models.URLField(blank=True)

    class Meta:
        unique_together = ('reference_number', 'publication')
        ordering = ['reference_number']
        default_related_name = 'references'

    def __str__(self):
        return '[{}] {}, {}'.format(self.reference_number, self.authors[:30], self.citation[:30])


class OrgPubFraction(models.Model):
    """
    Associates a fraction of the funding credit for a given publication to an Organization,
    to help answer the question: who funded this research?

    Fractions for a given publication should sum up to one.

    This data is used to compile publicly-displayed information on Organizations
    as well as to set suggested contributions from Partners.

    To be set (ideally) during production phase, based on information provided by the authors.
    """
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE,
                                     related_name='pubfractions', blank=True, null=True)
    publication = models.ForeignKey('journals.Publication', on_delete=models.CASCADE,
                                    related_name='pubfractions')
    fraction = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal('0.000'))

    class Meta:
        unique_together = (('organization', 'publication'),)
