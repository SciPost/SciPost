from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


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
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS, default='E')
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS, default='A')
    open_for_commenting = models.BooleanField(default=True)
    pub_title = models.CharField(max_length=300, verbose_name='title')
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)', blank=True)
    pub_DOI_link = models.URLField(verbose_name='DOI link to the original publication', blank=True)
    author_list = models.CharField(max_length=1000)
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField (Contributor, blank=True, related_name='authors_com')
    authors_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_com_claims')
    authors_false_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_com_false_claims')
    pub_date = models.DateField(verbose_name='date of original publication')
    pub_abstract = models.TextField(verbose_name='abstract')
    latest_activity = models.DateTimeField(default=timezone.now)

    def __str__ (self):
        return self.pub_title

    def header_as_table (self):
        # for display in Commentary page itself
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>' + self.pub_title + '</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>' + self.author_list + '</td></tr>'
        if self.type == 'published':
            header += '<tr><td>DOI: </td><td>&nbsp;</td><td><a href="' + self.pub_DOI_link + '" target="_blank">' + self.pub_DOI_link + '</a></td></tr>'
        elif self.type == 'preprint':
            header += '<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="' + self.arxiv_link + '">' + self.arxiv_link + '</a></td></tr>'
        header += '<tr><td>Date: </td><td>&nbsp;</td><td>' + str(self.pub_date) + '</td></tr>'
        header += '</table>'
        return header

    def header_as_li (self):
        # for display in search lists
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/commentary/' + str(self.id) + '" class="pubtitleli">' + self.pub_title + '</a></p>'
        header += '<p>by ' + self.author_list + '</p><p> (published ' + str(self.pub_date) + ') - latest activity: ' + self.latest_activity.strftime('%Y-%m-%d %H:%M') + '</p></div>'
        header += '</div></li>'
        return header
