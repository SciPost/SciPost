from django.contrib.postgres.fields import JSONField
from django.db import models
from django.http import Http404
from django.template import Template, Context
from django.utils import timezone

from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from scipost.models import ChoiceArrayField, Contributor


class UnregisteredAuthor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return self.last_name + ', ' + self.first_name


SCIPOST_JOURNALS = (
    ('SciPost Physics Select', 'SciPost Physics Select'),
    ('SciPost Physics', 'SciPost Physics'),
    ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes'),
    )
journals_dict = dict(SCIPOST_JOURNALS)


class JournalNameError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


def journal_name_abbrev_citation(journal_name):
    if journal_name == 'SciPost Physics':
        return 'SciPost Phys.'
    elif journal_name == 'SciPost Physics Select':
        return 'SciPost Phys. Sel.'
    elif journal_name == 'SciPost Physics Lecture Notes':
        return 'SciPost Phys. Lect. Notes'
    else:
        raise JournalNameError(journal_name)


def journal_name_abbrev_doi(journal_name):
    if journal_name == 'SciPost Physics':
        return 'SciPostPhys'
    elif journal_name == 'SciPost Physics Select':
        return 'SciPostPhysSel'
    elif journal_name == 'SciPost Physics Lecture Notes':
        return 'SciPostPhysLectNotes'
    else:
        raise JournalNameError(journal_name)


class PaperNumberError(Exception):
    def __init__(self, nr):
        self.nr = nr

    def __str__(self):
        return self.nr


def paper_nr_string(nr):
    if nr < 10:
        return '00' + str(nr)
    elif nr < 100:
        return '0' + str(nr)
    elif nr < 1000:
        return str(nr)
    else:
        raise PaperNumberError(nr)


class PaperNumberingError(Exception):
    def __init__(self, nr):
        self.nr = nr

    def __str__(self):
        return self.nr


SCIPOST_JOURNALS_SUBMIT = (  # Same as SCIPOST_JOURNALS, but SP Select deactivated
    ('SciPost Physics', 'SciPost Physics'),
    ('SciPost Physics Lecture Notes', 'SciPost Physics Lecture Notes'),
    )
journals_submit_dict = dict(SCIPOST_JOURNALS_SUBMIT)

SCIPOST_JOURNALS_DOMAINS = (
    ('E', 'Experimental'),
    ('T', 'Theoretical'),
    ('C', 'Computational'),
    ('ET', 'Exp. & Theor.'),
    ('EC', 'Exp. & Comp.'),
    ('TC', 'Theor. & Comp.'),
    ('ETC', 'Exp., Theor. & Comp.'),
)
journals_domains_dict = dict(SCIPOST_JOURNALS_DOMAINS)

SCIPOST_JOURNALS_SPECIALIZATIONS = (
    ('A', 'Atomic, Molecular and Optical Physics'),
    ('B', 'Biophysics'),
    ('C', 'Condensed Matter Physics'),
    ('F', 'Fluid Dynamics'),
    ('G', 'Gravitation, Cosmology and Astroparticle Physics'),
    ('H', 'High-Energy Physics'),
    ('M', 'Mathematical Physics'),
    ('N', 'Nuclear Physics'),
    ('Q', 'Quantum Statistical Mechanics'),
    ('S', 'Statistical and Soft Matter Physics'),
    )
journals_spec_dict = dict(SCIPOST_JOURNALS_SPECIALIZATIONS)


class Journal(models.Model):
    name = models.CharField(max_length=100, choices=SCIPOST_JOURNALS,
                            unique=True)
    doi_string = models.CharField(max_length=200, blank=True, null=True)
    issn = models.CharField(max_length=16, default='2542-4653')

    def __str__(self):
        return self.name


class Volume(models.Model):
    in_journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    doi_string = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        unique_together = ('number', 'in_journal')

    def __str__(self):
        return str(self.in_journal) + ' Vol. ' + str(self.number)


STATUS_DRAFT = 'draft'
STATUS_PUBLISHED = 'published'
ISSUE_STATUSES = (
    (STATUS_DRAFT, 'Draft'),
    (STATUS_PUBLISHED, 'Published'),
)


class IssueManager(models.Manager):
    def get_published(self, *args, **kwargs):
        try:
            return self.published(*args, **kwargs)[0]
        except IndexError:
            raise Http404

    def published(self, journal=None, **kwargs):
        issues = self.filter(status=STATUS_PUBLISHED, **kwargs)
        if journal:
            issues.filter(in_volume__in_journal__name=journal)
        return issues

    def in_draft(self, journal=None, **kwargs):
        issues = self.filter(status=STATUS_DRAFT, **kwargs)
        if journal:
            issues.filter(in_volume__in_journal__name=journal)
        return issues

    def get_current_issue(self, *args, **kwargs):
        return self.published(start_date__lte=timezone.now(),
                              until_date__gte=timezone.now(),
                              **kwargs).order_by('-until_date').first()


class Issue(models.Model):
    in_volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ISSUE_STATUSES, default=STATUS_PUBLISHED)
    doi_string = models.CharField(max_length=200, blank=True, null=True)
    # absolute path on filesystem: (JOURNALS_DIR)/journal/vol/issue/
    path = models.CharField(max_length=200)

    objects = IssueManager()

    class Meta:
        unique_together = ('number', 'in_volume')

    def __str__(self):
        text = str(self.in_volume) + ' issue ' + str(self.number)
        text += self.period_as_string()
        if self.status == STATUS_DRAFT:
            text += ' (In draft)'
        return text

    def period_as_string(self):
        if self.start_date.month == self.until_date.month:
            return ' (' + self.until_date.strftime('%B') + ' ' + self.until_date.strftime('%Y') + ')'
        else:
            return (' (' + self.start_date.strftime('%B') + '-' + self.until_date.strftime('%B') +
                    ' ' + self.until_date.strftime('%Y') + ')')

    def period(self):
        text = 'up to {{ until_month }} {{ year }}'
        template = Template(text)
        context = Context({'until_month': self.start_date.strftime('%B'),
                           'year': self.until_date.strftime('%Y')})
        return template.render(context)


class PublicationManager(models.Manager):
    def get_published(self, *args, **kwargs):
        try:
            return self.published(*args, **kwargs)[0]
        except IndexError:
            raise Http404

    def published(self, **kwargs):
        return self.filter(in_issue__status=STATUS_PUBLISHED, **kwargs)

    def in_draft(self, **kwargs):
        return self.filter(in_issue__status=STATUS_DRAFT, **kwargs)


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
    doi_label = models.CharField(max_length=200, blank=True, null=True)  # Used for file name
    doi_string = models.CharField(max_length=200, blank=True, null=True)
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

    def citation(self):
        return (journal_name_abbrev_citation(self.in_issue.in_volume.in_journal.name)
                + ' ' + str(self.in_issue.in_volume.number)
                + ', ' + paper_nr_string(self.paper_nr)
                + ' (' + self.publication_date.strftime('%Y') + ')')

    def citation_for_web(self):
        citation = ('{{ abbrev }} <strong>{{ volume_nr }}</strong>'
                    ', {{ paper_nr }} ({{ year }})')
        template = Template(citation)
        context = Context(
            {'abbrev': journal_name_abbrev_citation(self.in_issue.in_volume.in_journal.name),
             'volume_nr': str(self.in_issue.in_volume.number),
             'issue_nr': str(self.in_issue.number),
             'paper_nr': paper_nr_string(self.paper_nr),
             'year': self.publication_date.strftime('%Y'), })
        return template.render(context)

    def citation_for_web_linked(self):
        citation = ('<a href="{% url \'scipost:publication_detail\' doi_string=doi_string %}">'
                    '{{ abbrev }} <strong>{{ volume_nr }}</strong>'
                    ', {{ paper_nr }} ({{ year }})')
        template = Template(citation)
        context = Context(
            {'doi_string': self.doi_string,
             'abbrev': journal_name_abbrev_citation(self.in_issue.in_volume.in_journal.name),
             'volume_nr': str(self.in_issue.in_volume.number),
             'issue_nr': str(self.in_issue.number),
             'paper_nr': paper_nr_string(self.paper_nr),
             'year': self.publication_date.strftime('%Y'), })
        return template.render(context)

    def header_as_li(self):
        header = ('<div class="publicationHeader">'
                  '<h3 class="publicationTitle"><a href="{% url \'scipost:publication_detail\' doi_string=doi_string %}">{{ title }}</a></h3>'
                  '<p class="publicationAuthors">{{ author_list }}</p>'
                  '<p class="publicationReference">{{ citation }} &nbsp;&nbsp;'
                  '|&nbsp;published {{ pub_date }}</p>'
                  '<p class="publicationAbstract">{{ abstract }}</p>'
                  '<ul class="publicationClickables">'
                  '<li><button class="btn btn-secondary toggleAbstractButton">Toggle abstract</button></li>'
                  '<li class="publicationPDF"><a href="{% url \'scipost:publication_pdf\' doi_string=doi_string %}" target="_blank">pdf</a></li>'
                  '</ul>'
                  '</div>')
        template = Template(header)
        context = Context({
            'doi_string': self.doi_string,
            'title': self.title,
            'author_list': self.author_list,
            'citation': self.citation,
            'pub_date': self.publication_date.strftime('%d %B %Y'),
            'abstract': self.abstract,
        })
        return template.render(context)

    def details(self):
        """
        This method is called from the publication_detail template.
        It provides all the details for a publication.
        """
        pub_details = (
            '<div class="row"><div class="col-12">'
            '<h3 class="publicationTitle">'
            '<a href="{% url \'scipost:publication_detail\' doi_string=doi_string %}">{{ title }}</a>'
            '</h3>'
            '<p class="publicationAuthors">{{ author_list }}</p>'
            '<p class="publicationReference">{{ citation }} &nbsp;&nbsp;'
            '|&nbsp;published {{ pub_date}}</p>'
            '<ul class="publicationClickables">'
            '<li>doi:  {{ doi_string }}</li>'
            '<li class="publicationPDF">'
            '<a href="{% url \'scipost:publication_pdf\' doi_string=doi_string %}" target="_blank">pdf</a>'
            '</li>'
            '<li><a href="#openModal">BiBTeX</a></li>'
            '<li><a href="{% url \'submissions:submission\' arxiv_identifier_w_vn_nr='
            'arxiv_identifier_w_vn_nr %}">Submissions/Reports</a></li>'
            '</ul></div></div>'
            '<div class="row"><div class="col-12"><hr>'
            '<h3>Abstract:</h3>'
            '<p class="publicationAbstract">{{ abstract }}</p>'
            '<div id="openModal" class="modalDialog"><div>'
            '<a href="#close" title="Close" class="close">X</a>'
            '<h2>BiBTeX</h2><p>{{ BiBTeX|linebreaks }}</p></div></div>'
            '</div></div>'
        )
        template = Template(pub_details)
        context = Context({
            'title': self.title,
            'author_list': self.author_list,
            'citation': self.citation_for_web,
            'pub_date': self.publication_date.strftime('%d %B %Y'),
            'abstract': self.abstract,
            'doi_string': self.doi_string,
            'BiBTeX': self.BiBTeX_entry,
            'arxiv_identifier_w_vn_nr': self.accepted_submission.arxiv_identifier_w_vn_nr
        })
        return template.render(context)

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
                ' for ' + self.publication.doi_string)
