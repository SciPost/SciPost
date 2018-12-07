__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Min, Sum, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse

from .behaviors import (
    doi_journal_validator, doi_volume_validator, doi_issue_validator, doi_publication_validator)
from .constants import (
    SCIPOST_JOURNALS, SCIPOST_JOURNALS_DOMAINS, STATUS_DRAFT, STATUS_PUBLISHED, ISSUE_STATUSES,
    PUBLICATION_PUBLISHED, CCBY4, CC_LICENSES, CC_LICENSES_URI, PUBLICATION_STATUSES,
    JOURNAL_STRUCTURE, ISSUES_AND_VOLUMES, ISSUES_ONLY)
from .helpers import paper_nr_string, journal_name_abbrev_citation
from .managers import IssueQuerySet, PublicationQuerySet, JournalQuerySet

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.fields import ChoiceArrayField



################
# Journals etc #
################

class UnregisteredAuthor(models.Model):
    """UnregisteredAuthor is a replacement for a Contributor if an author has not registered."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile = models.ForeignKey(
        'profiles.Profile', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.last_name + ', ' + self.first_name


class PublicationAuthorsTable(models.Model):
    """PublicationAuthorsTable is an ordered link between people and Publications."""

    publication = models.ForeignKey('journals.Publication', related_name='authors')
    unregistered_author = models.ForeignKey('journals.UnregisteredAuthor', null=True, blank=True,
                                            related_name='+')
    contributor = models.ForeignKey('scipost.Contributor', null=True, blank=True, related_name='+')
    affiliations = models.ManyToManyField('organizations.Organization', blank=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)

    def __str__(self):
        if self.contributor:
            return str(self.contributor)
        elif self.unregistered_author:
            return str(self.unregistered_author)

    def save(self, *args, **kwargs):
        """Auto increment order number if not explicitly set."""
        if not self.order:
            self.order = self.publication.authors.count() + 1
        return super().save(*args, **kwargs)

    @property
    def is_registered(self):
        """Check if author is registered at SciPost."""
        return self.contributor is not None

    @property
    def first_name(self):
        """Return first name of author."""
        if self.contributor:
            return self.contributor.user.first_name
        if self.unregistered_author:
            return self.unregistered_author.first_name

    @property
    def last_name(self):
        """Return last name of author."""
        if self.contributor:
            return self.contributor.user.last_name
        if self.unregistered_author:
            return self.unregistered_author.last_name


class Journal(models.Model):
    """Journal is a container of Publications with a unique issn and doi_label.

    Publications may be categorized into issues or issues and volumes.
    """

    name = models.CharField(max_length=100, choices=SCIPOST_JOURNALS, unique=True)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_journal_validator])
    issn = models.CharField(max_length=16, default='2542-4653', blank=True)
    active = models.BooleanField(default=True)
    structure = models.CharField(max_length=2,
                                 choices=JOURNAL_STRUCTURE, default=ISSUES_AND_VOLUMES)
    refereeing_period = models.DurationField(default=datetime.timedelta(days=28))

    objects = JournalQuerySet.as_manager()

    def __str__(self):
        return self.get_name_display()

    def get_absolute_url(self):
        """Return Journal's homepage url."""
        return reverse('scipost:landing_page', args=(self.doi_label,))

    @property
    def doi_string(self):
        """Return DOI including the SciPost registrant prefix."""
        return '10.21468/' + self.doi_label

    @property
    def has_issues(self):
        return self.structure in (ISSUES_AND_VOLUMES, ISSUES_ONLY)

    @property
    def has_volumes(self):
        return self.structure in (ISSUES_AND_VOLUMES)

    @property
    def abbreviation_citation(self):
        return journal_name_abbrev_citation(self.name)

    def get_issues(self):
        if self.structure == ISSUES_AND_VOLUMES:
            return Issue.objects.filter(in_volume__in_journal=self).published()
        elif self.structure == ISSUES_ONLY:
            return self.issues.published()
        return Issue.objects.none()

    def get_publications(self):
        if self.structure == ISSUES_AND_VOLUMES:
            return Publication.objects.filter(in_issue__in_volume__in_journal=self)
        elif self.structure == ISSUES_ONLY:
            return Publication.objects.filter(in_issue__in_journal=self)
        return self.publications.all()

    def nr_publications(self, tier=None):
        publications = Publication.objects.filter(in_issue__in_volume__in_journal=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        return publications.count()

    def avg_processing_duration(self):
        duration = Publication.objects.filter(
            in_issue__in_volume__in_journal=self).aggregate(
                avg=Avg(F('publication_date') - F('submission_date')))['avg']
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Return the citation rate in units of nr citations per article per year."""
        publications = Publication.objects.filter(in_issue__in_volume__in_journal=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return (ncites * 365.25/deltat)

    def citedby_impact_factor(self, year):
        """Compute the impact factor for a given year YYYY, from Crossref cited-by data.

        This is defined as the total number of citations in year YYYY
        for all papers published in years YYYY-1 and YYYY-2, divided
        by the number of papers published in year YYYY.
        """
        publications = self.get_publications().filter(
            models.Q(publication_date__year=int(year)-1) |
            models.Q(publication_date__year=int(year)-2))
        nrpub = publications.count()
        if nrpub == 0:
            return 0
        ncites = 0
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                for citation in pub.citedby:
                    if citation['year'] == year:
                        ncites += 1
        return ncites/nrpub

class Volume(models.Model):
    """A Volume may be used as a subgroup of Publications related to a specific Issue object."""

    in_journal = models.ForeignKey('journals.Journal', on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_volume_validator])

    class Meta:
        default_related_name = 'volumes'
        ordering = ('-until_date',)
        unique_together = ('number', 'in_journal')

    def __str__(self):
        return str(self.in_journal) + ' Vol. ' + str(self.number)

    def clean(self):
        """Check if the Volume is assigned to a valid Journal."""
        if not self.in_journal.has_volumes:
            raise ValidationError({
                'in_journal': ValidationError('This journal does not allow for the use of Volumes',
                                              code='invalid'),
            })

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    def nr_publications(self, tier=None):
        publications = Publication.objects.filter(in_issue__in_volume=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        return publications.count()

    def avg_processing_duration(self):
        duration = Publication.objects.filter(
            in_issue__in_volume=self).aggregate(
                avg=Avg(F('publication_date') - F('submission_date')))['avg']
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Returns the citation rate in units of nr citations per article per year."""
        publications = Publication.objects.filter(in_issue__in_volume=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return (ncites * 365.25 / deltat)


class Issue(models.Model):
    """An Issue may be used as a subgroup of Publications related to a specific Journal object."""

    in_journal = models.ForeignKey(
        'journals.Journal', on_delete=models.CASCADE, null=True, blank=True,
        help_text='Assign either an Volume or Journal to the Issue')
    in_volume = models.ForeignKey(
        'journals.Volume', on_delete=models.CASCADE, null=True, blank=True,
        help_text='Assign either an Volume or Journal to the Issue')
    number = models.PositiveSmallIntegerField()
    slug = models.SlugField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ISSUE_STATUSES, default=STATUS_PUBLISHED)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_issue_validator])

    # absolute path on filesystem: (JOURNALS_DIR)/journal/vol/issue/
    path = models.CharField(max_length=200)

    objects = IssueQuerySet.as_manager()

    class Meta:
        default_related_name = 'issues'
        ordering = ('-until_date',)
        unique_together = ('number', 'in_volume')

    def __str__(self):
        text = self.issue_number
        if hasattr(self, 'proceedings'):
            return text
        text += ' (%s)' % self.period_as_string
        if self.status == STATUS_DRAFT:
            text += ' (In draft)'
        return text

    def clean(self):
        """Check if either a Journal or Volume is assigned to the Issue."""
        if not (self.in_journal or self.in_volume):
            raise ValidationError({
                'in_journal': ValidationError('Either assign a Journal or Volume to this Issue',
                                              code='required'),
                'in_volume': ValidationError('Either assign a Journal or Volume to this Issue',
                                             code='required'),
            })
        if self.in_journal and not self.in_journal.has_issues:
            raise ValidationError({
                'in_journal': ValidationError('This journal does not allow for the use of Issues',
                                              code='invalid'),
            })

    def get_absolute_url(self):
        return reverse('scipost:issue_detail', args=[self.doi_label])

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    @property
    def issue_number(self):
        if self.in_volume:
            return '%s issue %s' % (self.in_volume, self.number)
        return '%s issue %s' % (self.in_journal, self.number)

    @property
    def short_str(self):
        if self.in_volume:
            return 'Vol. %s issue %s' % (self.in_volume.number, self.number)
        return 'Issue %s' % self.number

    @property
    def period_as_string(self):
        if self.start_date.month == self.until_date.month:
            return '%s %s' % (self.until_date.strftime('%B'), self.until_date.strftime('%Y'))
        return '%s - %s' % (self.start_date.strftime('%B'), self.until_date.strftime('%B %Y'))

    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today and self.until_date >= today

    def nr_publications(self, tier=None):
        publications = Publication.objects.filter(in_issue=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        return publications.count()

    def avg_processing_duration(self):
        duration = Publication.objects.filter(
            in_issue=self).aggregate(
                avg=Avg(F('publication_date') - F('submission_date')))['avg']
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Return the citation rate in units of nr citations per article per year."""
        publications = Publication.objects.filter(in_issue=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return (ncites * 365.25 / deltat)


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
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    secondary_areas = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS), blank=True, null=True)

    # Authors
    authors_registered = models.ManyToManyField('scipost.Contributor', blank=True,
                                                through='PublicationAuthorsTable',
                                                through_fields=('publication', 'contributor'))
    authors_unregistered = models.ManyToManyField('journals.UnregisteredAuthor', blank=True,
                                                  through='PublicationAuthorsTable',
                                                  through_fields=(
                                                    'publication',
                                                    'unregistered_author'))
    authors_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                            related_name='claimed_publications')
    authors_false_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                                  related_name='false_claimed_publications')

    cc_license = models.CharField(max_length=32, choices=CC_LICENSES, default=CCBY4)

    # Funders
    grants = models.ManyToManyField('funders.Grant', blank=True)
    funders_generic = models.ManyToManyField('funders.Funder', blank=True)  # not linked to a grant
    institutions = models.ManyToManyField('affiliations.Institution', blank=True)
    pubfractions_confirmed_by_authors = models.BooleanField(default=False)

    # Metadata
    metadata = JSONField(default={}, blank=True, null=True)
    metadata_xml = models.TextField(blank=True)  # for Crossref deposit
    metadata_DOAJ = JSONField(default={}, blank=True, null=True)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_publication_validator])
    BiBTeX_entry = models.TextField(blank=True)
    doideposit_needs_updating = models.BooleanField(default=False)
    citedby = JSONField(default={}, blank=True, null=True)
    number_of_citations = models.PositiveIntegerField(default=0)

    # Topics for semantic linking
    topics = models.ManyToManyField('ontology.Topic', blank=True)

    # Date fields
    submission_date = models.DateField(verbose_name='submission date')
    acceptance_date = models.DateField(verbose_name='acceptance date')
    publication_date = models.DateField(verbose_name='publication date')
    latest_citedby_update = models.DateTimeField(null=True, blank=True)
    latest_metadata_update = models.DateTimeField(blank=True, null=True)
    latest_activity = models.DateTimeField(default=timezone.now)

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
                journal=self.in_issue.in_volume.in_journal.abbreviation_citation,
                volume=self.in_issue.in_volume.number,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime('%Y'))
        elif self.in_issue and self.in_issue.in_journal:
            return '{journal} {issue}, {paper_nr} ({year})'.format(
                journal=self.in_issue.in_journal.abbreviation_citation,
                issue=self.in_issue.number,
                paper_nr=self.get_paper_nr(),
                year=self.publication_date.strftime('%Y'))
        elif self.in_journal:
            return '{journal} {paper_nr} ({year})'.format(
                journal=self.in_journal.abbreviation_citation,
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

    def get_similar_publications(self):
        """Return 4 Publications with same subject area."""
        return Publication.objects.published().filter(
            subject_area=self.subject_area).exclude(id=self.id)[:4]

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


class Deposit(models.Model):
    """
    Each time a Crossref deposit is made for a Publication,
    a Deposit object instance is created containing the Publication's
    current version of the metadata_xml field.
    All deposit history is thus contained here.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=40)
    doi_batch_id = models.CharField(max_length=40)
    metadata_xml = models.TextField(blank=True)
    metadata_xml_file = models.FileField(blank=True, null=True, max_length=512)
    deposition_date = models.DateTimeField(blank=True, null=True)
    response_text = models.TextField(blank=True)
    deposit_successful = models.NullBooleanField(default=None)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        _str = ''
        if self.deposition_date:
            _str += '%s for ' % self.deposition_date.strftime('%Y-%m-%D')
        return _str + self.publication.doi_label


class DOAJDeposit(models.Model):
    """
    For the Directory of Open Access Journals.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=40)
    metadata_DOAJ = JSONField()
    metadata_DOAJ_file = models.FileField(blank=True, null=True, max_length=512)
    deposition_date = models.DateTimeField(blank=True, null=True)
    response_text = models.TextField(blank=True, null=True)
    deposit_successful = models.NullBooleanField(default=None)

    class Meta:
        verbose_name = 'DOAJ deposit'

    def __str__(self):
        return ('DOAJ deposit for ' + self.publication.doi_label)


class GenericDOIDeposit(models.Model):
    """
    Instances of this class represent Crossref deposits for non-publication
    objects such as Reports, Comments etc.
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    timestamp = models.CharField(max_length=40, default='')
    doi_batch_id = models.CharField(max_length=40, default='')
    metadata_xml = models.TextField(blank=True, null=True)
    deposition_date = models.DateTimeField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    deposit_successful = models.NullBooleanField(default=None)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return 'GenericDOIDeposit for %s %s' % (self.content_type, str(self.content_object))
