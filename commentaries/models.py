from django.utils import timezone
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.template import Template, Context

from journals.models import SCIPOST_JOURNALS_DOMAINS, SCIPOST_JOURNALS_SPECIALIZATIONS
from scipost.models import TimeStampedModel, Contributor
from scipost.models import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS

COMMENTARY_TYPES = (
    ('published', 'published paper'),
    ('preprint', 'arXiv preprint'),
    )


class CommentaryManager(models.Manager):
    def vetted(self, **kwargs):
        return self.filter(vetted=True, **kwargs)

    def awaiting_vetting(self, **kwargs):
        return self.filter(vetted=False, **kwargs)


class Commentary(TimeStampedModel):
    """
    A Commentary contains all the contents of a SciPost Commentary page for a given publication.
    """
    requested_by = models.ForeignKey(
        Contributor, blank=True, null=True,
        on_delete=models.CASCADE, related_name='requested_by')
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey(Contributor, blank=True, null=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=9, choices=COMMENTARY_TYPES)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    subject_area = models.CharField(
        max_length=10, choices=SCIPOST_SUBJECT_AREAS,
        default='Phys:QP')
    open_for_commenting = models.BooleanField(default=True)
    pub_title = models.CharField(max_length=300, verbose_name='title')
    arxiv_identifier = models.CharField(
        max_length=100, verbose_name="arXiv identifier (including version nr)",
        blank=True, null=True)
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)', blank=True)
    pub_DOI = models.CharField(
        max_length=200, verbose_name='DOI of the original publication',
        blank=True, null=True)
    pub_DOI_link = models.URLField(
        verbose_name='DOI link to the original publication',
        blank=True)
    metadata = JSONField(default={}, blank=True, null=True)
    arxiv_or_DOI_string = models.CharField(
        max_length=100,
        verbose_name='string form of arxiv nr or DOI for commentary url',
        default='')
    author_list = models.CharField(max_length=1000)

    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField(
        Contributor, blank=True,
        related_name='authors_com')
    authors_claims = models.ManyToManyField(
        Contributor, blank=True,
        related_name='authors_com_claims')
    authors_false_claims = models.ManyToManyField(
        Contributor, blank=True,
        related_name='authors_com_false_claims')
    journal = models.CharField(max_length=300, blank=True, null=True)
    volume = models.CharField(max_length=50, blank=True, null=True)
    pages = models.CharField(max_length=50, blank=True, null=True)
    pub_date = models.DateField(
        verbose_name='date of original publication',
        blank=True, null=True)
    pub_abstract = models.TextField(verbose_name='abstract')

    objects = CommentaryManager()

    class Meta:
        verbose_name_plural = 'Commentaries'

    def __str__(self):
        return self.pub_title

    def header_as_table(self):
        # for display in Commentary page itself
        header = ('<table>'
                  '<tr><td>Title: </td><td>&nbsp;</td><td>{{ pub_title }}</td></tr>'
                  '<tr><td>Author(s): </td><td>&nbsp;</td><td>{{ author_list }}</td></tr>'
                  '<tr><td>As Contributors: </td><td>&nbsp;</td>')
        if self.authors.all():
            header += '<td>'
            for auth in self.authors.all():
                header += ('<a href="/contributor/' + str(auth.id) + '">' + auth.user.first_name
                           + ' ' + auth.user.last_name + '</a>,&nbsp;')
            header += '</td>'
        else:
            header += '<td>(none claimed)</td>'
        header += '</tr>'
        if self.type == 'published':
            header += ('<tr><td>Journal ref.: </td><td>&nbsp;</td><td>{{ journal }} {{ volume }}, '
                       '{{ pages }}</td></tr>'
                       '<tr><td>DOI: </td><td>&nbsp;</td><td><a href="{{ pub_DOI_link }}" '
                       'target="_blank">{{ pub_DOI_link }}</a></td></tr>')
        elif self.type == 'preprint':
            header += ('<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="{{ arxiv_link }}">'
                       '{{ arxiv_link }}</a></td></tr>')
        if self.pub_date:
            header += '<tr><td>Date: </td><td>&nbsp;</td><td>{{ pub_date }}</td></tr>'
        header += '</table>'
        template = Template(header)
        context = Context({
            'pub_title': self.pub_title, 'author_list': self.author_list,
        })
        if self.type == 'published':
            context['journal'] = self.journal
            context['volume'] = self.volume
            context['pages'] = self.pages
            context['pub_DOI_link'] = self.pub_DOI_link
            context['pub_date'] = self.pub_date
        elif self.type == 'preprint':
            context['arxiv_link'] = self.arxiv_link
        return template.render(context)

    def header_as_li(self):
        # for display in search lists
        context = Context({'scipost_url': self.scipost_url(), 'pub_title': self.pub_title,
                           'author_list': self.author_list,
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M')})
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p><a href="{{ scipost_url }}" '
                  'class="pubtitleli">{{ pub_title }}</a></p>'
                  '<p>by {{ author_list }}')
        if self.type == 'published':
            header += ', {{ journal }} {{ volume }}, {{ pages }}'
            context['journal'] = self.journal
            context['volume'] = self.volume
            context['pages'] = self.pages
        elif self.type == 'preprint':
            header += ', <a href="{{ arxiv_link }}">{{ arxiv_link }}</a>'
            context['arxiv_link'] = self.arxiv_link
        header += '</p>'
        if self.pub_date:
            header += '<p> (published {{ pub_date }}) - '
            context['pub_date'] = str(self.pub_date)
        header += ('latest activity: {{ latest_activity }}</p>'
                   #'</div></div>'
                   '</li>')
        template = Template(header)

        return template.render(context)

    def simple_header_as_li(self):
        # for display in Lists
        context = Context({'scipost_url': self.scipost_url(), 'pub_title': self.pub_title,
                           'author_list': self.author_list})
        header = ('<li>'
                  '<p><a href="{{ scipost_url }}" '
                  'class="pubtitleli">{{ pub_title }}</a></p>'
                  '<p>by {{ author_list }}')
        if self.type == 'published':
            header += ', {{ journal }} {{ volume }}, {{ pages }}'
            context['journal'] = self.journal
            context['volume'] = self.volume
            context['pages'] = self.pages
        elif self.type == 'preprint':
            header += ', <a href="{{ arxiv_link }}">{{ arxiv_link }}</a>'
            context['arxiv_link'] = self.arxiv_link
        header += '</p>'
        header += '</li>'
        template = Template(header)
        return template.render(context)

    def parse_links_into_urls(self):
        """ Takes the arXiv nr or DOI and turns it into the urls """
        if self.pub_DOI:
            self.arxiv_or_DOI_string = self.pub_DOI
            self.pub_DOI_link = 'http://dx.doi.org/' + self.pub_DOI
        elif self.arxiv_identifier:
            self.arxiv_or_DOI_string = 'arXiv:' + self.arxiv_identifier
            self.arxiv_link = 'http://arxiv.org/abs/' + self.arxiv_identifier
        else: # should never come here
            pass
        self.save()

    def scipost_url(self):
        """ Returns the url of the SciPost Commentary Page """
        return '/commentary/' + self.arxiv_or_DOI_string

    def scipost_url_full(self):
        """ Returns the url of the SciPost Commentary Page """
        return 'https://scipost.org/commentary/' + self.arxiv_or_DOI_string
