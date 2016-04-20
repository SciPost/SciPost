from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.template import Template, Context

from journals.models import SCIPOST_JOURNALS_DOMAINS, SCIPOST_JOURNALS_SPECIALIZATIONS
from scipost.models import Contributor
from scipost.models import SCIPOST_DISCIPLINES



COMMENTARY_TYPES = (
    ('published', 'published paper'),
    ('preprint', 'arXiv preprint (at least 8 weeks old)'),
    )

class Commentary(models.Model):
    """ A Commentary contains all the contents of a SciPost Commentary page for a given publication. """
    requested_by = models.ForeignKey (Contributor, blank=True, null=True, related_name='requested_by')
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey (Contributor, blank=True, null=True)
    type = models.CharField(max_length=9, choices=COMMENTARY_TYPES) # published paper or arxiv preprint
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    open_for_commenting = models.BooleanField(default=True)
    pub_title = models.CharField(max_length=300, verbose_name='title')
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)', blank=True)
    pub_DOI_link = models.URLField(verbose_name='DOI link to the original publication', blank=True)
    arxiv_or_DOI_string = models.CharField(max_length=100, verbose_name='string form of arxiv nr or DOI for commentary url', default='')
    author_list = models.CharField(max_length=1000)
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField (Contributor, blank=True, related_name='authors_com')
    authors_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_com_claims')
    authors_false_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_com_false_claims')
    pub_date = models.DateField(verbose_name='date of original publication', blank=True, null=True)
    pub_abstract = models.TextField(verbose_name='abstract')
    latest_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Commentaries'


    def __str__ (self):
        return self.pub_title


    def header_as_table(self):
        # for display in Commentary page itself
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>{{ pub_title }}</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>{{ author_list }}</td></tr>'
        header += '<tr><td>As Contributors: </td><td>&nbsp;</td>'
        if self.authors.all():
            header += '<td>'
            for auth in self.authors.all():
                header += '<a href="/contributor/' + str(auth.id) + '">' + auth.user.first_name + ' ' + auth.user.last_name + '</a>,&nbsp;'
            header += '</td>'
        else:
            header += '<td>(none claimed)</td>'
        header += '</tr>'
        if self.type == 'published':
            header += '<tr><td>DOI: </td><td>&nbsp;</td><td><a href="{{ pub_DOI_link }}" target="_blank">{{ pub_DOI_link }}</a></td></tr>'
        elif self.type == 'preprint':
            header += '<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="{{ arxiv_link }}">{{ arxiv_link }}</a></td></tr>'
        if self.pub_date:
            header += '<tr><td>Date: </td><td>&nbsp;</td><td>{{ pub_date }}</td></tr>'
        header += '</table>'
        template = Template(header)
        context = Context({
                'pub_title': self.pub_title, 'author_list': self.author_list, 
                })
        if self.type == 'published':
            context['pub_DOI_link'] = self.pub_DOI_link
            context['pub_date'] = self.pub_date
        elif self.type == 'preprint':
            context['arxiv_link'] = self.arxiv_link
        return template.render(context)


    def header_as_li (self):
        # for display in search lists
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="{{ scipost_url }}" class="pubtitleli">{{ pub_title }}</a></p>'
        header += '<p>by {{ author_list }}</p>'
        if self.pub_date:
            header += '<p> (published {{ pub_date }}) - '
        header += 'latest activity: {{ latest_activity }}</p></div></div></li>'
        template = Template(header)
        context = Context({'scipost_url': self.scipost_url(), 'pub_title': self.pub_title,
                           'author_list': self.author_list, 
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M')})
        if self.pub_date:
            context['pub_date'] = str(self.pub_date)
        return template.render(context)


    def simple_header_as_li (self):
        # for display in Lists
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="{{ scipost_url }}" class="pubtitleli">{{ pub_title }}</a></p>'
        header += '<p>by {{ author_list }}</p>'
        header += '</div></div></li>'
        template = Template(header)
        context = Context({'scipost_url': self.scipost_url(), 'pub_title': self.pub_title,
                           'author_list': self.author_list})
        return template.render(context)


    def parse_link_into_url (self):
        """ Takes the arXiv nr or DOI and turns it into the url suffix """
        if self.pub_DOI_link:
            self.arxiv_or_DOI_string = str(self.pub_DOI_link)
            self.arxiv_or_DOI_string = self.arxiv_or_DOI_string.replace('http://dx.doi.org/', '')
        else:
            self.arxiv_or_DOI_string = str(self.arxiv_link)
            # Format required: either identifier arXiv:1234.56789v10 or old-style arXiv:cond-mat/9712001v1
            # strip: 
            self.arxiv_or_DOI_string = self.arxiv_or_DOI_string.replace('http://', '')
            # Old style: from arxiv.org/abs/1234.5678 into arXiv:1234.5678 (new identifier style)
            self.arxiv_or_DOI_string = self.arxiv_or_DOI_string.replace('arxiv.org/', '')
            self.arxiv_or_DOI_string = self.arxiv_or_DOI_string.replace('abs/', '')
            self.arxiv_or_DOI_string = self.arxiv_or_DOI_string.replace('pdf/', '')
            # make sure arXiv prefix is there:
            self.arxiv_or_DOI_string = 'arXiv:' + self.arxiv_or_DOI_string
        self.save()

    def scipost_url (self):
        """ Returns the url of the SciPost Commentary Page """
        return '/commentary/' + self.arxiv_or_DOI_string 

    def scipost_url_full (self):
        """ Returns the url of the SciPost Commentary Page """
        return 'https://scipost.org/commentary/' + self.arxiv_or_DOI_string 
