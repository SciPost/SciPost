from django.contrib.postgres.fields import JSONField
from django.db import models
from django.template import Template, Context
from django.utils import timezone
from django.urls import reverse

from .behaviors import doi_journal_validator, doi_volume_validator,\
                       doi_issue_validator, doi_publication_validator
from .constants import SCIPOST_JOURNALS, SCIPOST_JOURNALS_DOMAINS,\
                       STATUS_DRAFT, STATUS_PUBLISHED, ISSUE_STATUSES,\
                       PRODUCTION_STREAM_STATUS, PRODUCTION_EVENTS
from .helpers import paper_nr_string, journal_name_abbrev_citation
from .managers import IssueManager, PublicationManager, JournalManager

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor


##############
# Production #
##############

class ProductionStream(models.Model):
    submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE)
    opened = models.DateTimeField()

    def __str__(self):
        return str(self.submission)

    def total_duration(self):
        totdur = self.productionevent_set.all().aggregate(models.Sum('duration'))
        return totdur['duration__sum']


class ProductionEvent(models.Model):
    stream = models.ForeignKey(ProductionStream, on_delete=models.CASCADE)
    event = models.CharField(max_length=64, choices=PRODUCTION_EVENTS)
    comments = models.TextField(blank=True, null=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (str(self.stream.submission), self.get_event_display())


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
    issn = models.CharField(max_length=16, default='2542-4653')
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


class Volume(models.Model):
    in_journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
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


class Issue(models.Model):
    in_volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
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
        text = '%s issue %s' % (self.in_volume, self.number)
        text += self.period_as_string()
        if self.status == STATUS_DRAFT:
            text += ' (In draft)'
        return text

    def get_absolute_url(self):
        return reverse('scipost:issue_detail', args=[self.doi_label])

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

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


class Publication(models.Model):
    accepted_submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE)
    in_issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    paper_nr = models.PositiveSmallIntegerField()
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    secondary_areas = ChoiceArrayField(models.CharField(max_length=10,
                                                        choices=SCIPOST_SUBJECT_AREAS),
                                       blank=True, null=True)
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField(Contributor, blank=True, related_name='authors_pub')
    authors_unregistered = models.ManyToManyField(UnregisteredAuthor, blank=True,
                                                  related_name='authors_unregistered')
    first_author = models.ForeignKey(Contributor, blank=True, null=True, on_delete=models.CASCADE)
    first_author_unregistered = models.ForeignKey(UnregisteredAuthor, blank=True, null=True,
                                                  on_delete=models.CASCADE,
                                                  related_name='first_author_unregistered')
    authors_claims = models.ManyToManyField(Contributor, blank=True,
                                            related_name='authors_pub_claims')
    authors_false_claims = models.ManyToManyField(Contributor, blank=True,
                                                  related_name='authors_pub_false_claims')
    abstract = models.TextField()
    pdf_file = models.FileField(upload_to='UPLOADS/PUBLICATIONS/%Y/%m/', max_length=200)
    metadata = JSONField(default={}, blank=True, null=True)
    metadata_xml = models.TextField(blank=True, null=True)  # for Crossref deposit
    BiBTeX_entry = models.TextField(blank=True, null=True)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_publication_validator])
    submission_date = models.DateField(verbose_name='submission date')
    acceptance_date = models.DateField(verbose_name='acceptance date')
    publication_date = models.DateField(verbose_name='publication date')
    latest_activity = models.DateTimeField(default=timezone.now)
    citedby = JSONField(default={}, blank=True, null=True)

    objects = PublicationManager()

    def __str__(self):
        header = (self.citation() + ', '
                  + self.title[:30] + ' by ' + self.author_list[:30]
                  + ', published ' + self.publication_date.strftime('%Y-%m-%d'))
        return header

    def get_absolute_url(self):
        return reverse('scipost:publication_detail', args=[self.doi_label])

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

    def citations_as_ul(self):
        output = '<ul>'
        context = Context({})
        nr = 0
        for cit in self.citedby:
            output += '<li>{{ auth_' + str(nr) + ' }}'
            context['auth_' + str(nr)] = (cit['first_author_given_name']
                                          + ' ' + cit['first_author_surname'])
            if cit['multiauthors']:
                output += ' <em>et al.</em>'
            output += (', <em>{{ title_' + str(nr) + ' }}</em>, <br/>'
                       '{{ journal_abbrev_' + str(nr) + ' }}')
            context['title_' + str(nr)] = cit['article_title']
            context['journal_abbrev_' + str(nr)] = cit['journal_abbreviation']
            if cit['volume']:
                context['volume_' + str(nr)] = cit['volume']
                output += ' <strong>{{ volume_' + str(nr) + ' }}</strong>'
            output += ', '
            if cit['first_page']:
                output += '{{ first_page_' + str(nr) + ' }}'
                context['first_page_' + str(nr)] = cit['first_page']
            elif cit['item_number']:
                output += '{{ item_number_' + str(nr) + ' }}'
                context['item_number_' + str(nr)] = cit['item_number']
            output += (' ({{ year_' + str(nr) + ' }}) '
                       '<a href="https://doi.org/{{ doi_' + str(nr) + ' }}" '
                       'target="_blank">[Crossref]</a>')
            context['year_' + str(nr)] = cit['year']
            context['doi_' + str(nr)] = cit['doi']
            output += '</li>'
            nr += 1
        output += '</ul>'
        template = Template(output)
        return template.render(context)


class Deposit(models.Model):
    """
    Each time a Crossref deposit is made for a Publication,
    a Deposit object instance is created containing the Publication's
    current version of the metadata_xml field.
    All deposit history is thus contained here.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    doi_batch_id = models.CharField(max_length=40, default='')
    metadata_xml = models.TextField(blank=True, null=True)
    deposition_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return (self.deposition_date.strftime('%Y-%m-%D') +
                ' for 10.21468/' + self.publication.doi_label)
