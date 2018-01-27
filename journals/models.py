from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Avg, F
from django.utils import timezone
from django.urls import reverse

from .behaviors import doi_journal_validator, doi_volume_validator,\
                       doi_issue_validator, doi_publication_validator
from .constants import SCIPOST_JOURNALS, SCIPOST_JOURNALS_DOMAINS,\
                       STATUS_DRAFT, STATUS_PUBLISHED, ISSUE_STATUSES,\
                       CCBY4, CC_LICENSES, CC_LICENSES_URI
from .helpers import paper_nr_string, journal_name_abbrev_citation
from .managers import IssueManager, PublicationQuerySet, JournalManager

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.fields import ChoiceArrayField


################
# Journals etc #
################

class UnregisteredAuthor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return self.last_name + ', ' + self.first_name


class Journal(models.Model):
    name = models.CharField(max_length=100, choices=SCIPOST_JOURNALS, unique=True)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_journal_validator])
    issn = models.CharField(max_length=16, default='2542-4653', blank=True)
    active = models.BooleanField(default=True)

    objects = JournalManager()

    def __str__(self):
        return self.get_name_display()

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    def get_absolute_url(self):
        return reverse('scipost:landing_page', args=[self.doi_label])

    def get_abbreviation_citation(self):
        return journal_name_abbrev_citation(self.name)

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
        return duration.total_seconds() / 86400

    def citation_rate(self, tier=None):
        """
        Returns the citation rate in units of nr citations per article per year.
        """
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


class Volume(models.Model):
    in_journal = models.ForeignKey('journals.Journal', on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_volume_validator])

    class Meta:
        unique_together = ('number', 'in_journal')

    def __str__(self):
        return str(self.in_journal) + ' Vol. ' + str(self.number)

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
        return duration.total_seconds() / 86400

    def citation_rate(self, tier=None):
        """
        Returns the citation rate in units of nr citations per article per year.
        """
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
    in_volume = models.ForeignKey('journals.Volume', on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ISSUE_STATUSES, default=STATUS_PUBLISHED)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_issue_validator])
    # absolute path on filesystem: (JOURNALS_DIR)/journal/vol/issue/
    path = models.CharField(max_length=200)

    objects = IssueManager()

    class Meta:
        unique_together = ('number', 'in_volume')

    def __str__(self):
        text = self.issue_number
        if hasattr(self, 'proceedings'):
            return text
        text += self.period_as_string()
        if self.status == STATUS_DRAFT:
            text += ' (In draft)'
        return text

    def get_absolute_url(self):
        return reverse('scipost:issue_detail', args=[self.doi_label])

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    @property
    def issue_number(self):
        return '%s issue %s' % (self.in_volume, self.number)

    def short_str(self):
        return 'Vol. %s issue %s' % (self.in_volume.number, self.number)

    def period_as_string(self):
        if self.start_date.month == self.until_date.month:
            return ' (%s %s)' % (self.until_date.strftime('%B'), self.until_date.strftime('%Y'))
        else:
            return (' (' + self.start_date.strftime('%B') + '-' + self.until_date.strftime('%B') +
                    ' ' + self.until_date.strftime('%Y') + ')')

    def is_current(self):
        return self.start_date <= timezone.now().date() and\
               self.until_date >= timezone.now().date()

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
        return duration.total_seconds() / 86400

    def citation_rate(self, tier=None):
        """
        Returns the citation rate in units of nr citations per article per year.
        """
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
        return (ncites * 365.25/deltat)


class Publication(models.Model):
    """
    A Publication is an object directly related to an accepted Submission. It contains metadata,
    the actual publication file, author data, etc. etc.
    """
    # Publication data
    accepted_submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE,
                                               related_name='publication')
    in_issue = models.ForeignKey('journals.Issue', on_delete=models.CASCADE)
    paper_nr = models.PositiveSmallIntegerField()

    # Core fields
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    abstract = models.TextField()
    pdf_file = models.FileField(upload_to='UPLOADS/PUBLICATIONS/%Y/%m/', max_length=200)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    secondary_areas = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS), blank=True, null=True)

    # Authors
    authors = models.ManyToManyField('scipost.Contributor', blank=True,
                                     related_name='publications')
    authors_unregistered = models.ManyToManyField('journals.UnregisteredAuthor', blank=True,
                                                  related_name='publications')
    first_author = models.ForeignKey('scipost.Contributor', blank=True, null=True,
                                     on_delete=models.CASCADE,
                                     related_name='first_author_publications')
    first_author_unregistered = models.ForeignKey('journals.UnregisteredAuthor', blank=True, null=True,
                                                  on_delete=models.CASCADE,
                                                  related_name='first_author_publications')
    authors_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                            related_name='claimed_publications')
    authors_false_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                                  related_name='false_claimed_publications')

    cc_license = models.CharField(max_length=32, choices=CC_LICENSES, default=CCBY4)

    # Funders
    grants = models.ManyToManyField('funders.Grant', blank=True, related_name="publications")
    funders_generic = models.ManyToManyField(
        'funders.Funder', blank=True, related_name="publications")  # not linked to a grant
    institutions = models.ManyToManyField('affiliations.Institution',
                                          blank=True, related_name="publications")

    # Metadata
    metadata = JSONField(default={}, blank=True, null=True)
    metadata_xml = models.TextField(blank=True, null=True)  # for Crossref deposit
    metadata_DOAJ = JSONField(default={}, blank=True, null=True)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_publication_validator])
    BiBTeX_entry = models.TextField(blank=True, null=True)
    doideposit_needs_updating = models.BooleanField(default=False)
    citedby = JSONField(default={}, blank=True, null=True)

    # Date fields
    submission_date = models.DateField(verbose_name='submission date')
    acceptance_date = models.DateField(verbose_name='acceptance date')
    publication_date = models.DateField(verbose_name='publication date')
    latest_citedby_update = models.DateTimeField(null=True, blank=True)
    latest_metadata_update = models.DateTimeField(blank=True, null=True)
    latest_activity = models.DateTimeField(default=timezone.now)

    objects = PublicationQuerySet.as_manager()

    def __str__(self):
        header = (self.citation() + ', '
                  + self.title[:30] + ' by ' + self.author_list[:30]
                  + ', published ' + self.publication_date.strftime('%Y-%m-%d'))
        return header

    def get_absolute_url(self):
        return reverse('scipost:publication_detail', args=[self.doi_label])

    def get_cc_license_URI(self):
        for (key, val) in CC_LICENSES_URI:
            if key == self.cc_license:
                return val
        raise KeyError

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    def get_paper_nr(self):
        return paper_nr_string(self.paper_nr)

    def citation(self):
        return (self.in_issue.in_volume.in_journal.get_abbreviation_citation()
                + ' ' + str(self.in_issue.in_volume.number)
                + ', ' + self.get_paper_nr()
                + ' (' + self.publication_date.strftime('%Y') + ')')

    def citation_rate(self):
        """
        Returns the citation rate in units of nr citations per article per year.
        """
        if self.citedby and self.latest_citedby_update:
            ncites = len(self.citedby)
            deltat = (self.latest_citedby_update.date() - self.publication_date).days
            return (ncites * 365.25/deltat)
        else:
            return 0


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
    timestamp = models.CharField(max_length=40, default='')
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
