from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from scipost.models import *

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
    open_for_commenting = models.BooleanField(default=True)
    pub_title = models.CharField(max_length=300, verbose_name='title')
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)', blank=True)
    pub_DOI_link = models.URLField(verbose_name='DOI link to the original publication', blank=True)
    author_list = models.CharField(max_length=1000)
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField (Contributor, blank=True, related_name='authors_com')
    pub_date = models.DateField(verbose_name='date of original publication')
    pub_abstract = models.TextField(verbose_name='abstract')

    nr_clarity_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_validity_ratings = models.IntegerField(default=0)
    validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_rigour_ratings = models.IntegerField(default=0)
    rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_originality_ratings = models.IntegerField(default=0)
    originality_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_significance_ratings = models.IntegerField(default=0)
    significance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)

    latest_activity = models.DateTimeField(default=timezone.now)

    def __str__ (self):
        return self.pub_title

    def header_as_table (self):
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>' + self.pub_title + '</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>' + self.author_list + '</td></tr>'
        if self.type == 'published':
            header += '<tr><td>DOI: </td><td>&nbsp;</td><td><a href="' + self.pub_DOI_link + '">' + self.pub_DOI_link + '</a></td></tr>'
        elif self.type == 'preprint':
            header += '<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="' + self.arxiv_link + '">' + self.arxiv_link + '</a></td></tr>'
        header += '<tr><td>Date: </td><td>&nbsp;</td><td>' + str(self.pub_date) + '</td></tr>'
        header += '</table>'
        return header

    def header_as_li (self):
#        header = '<li><table><tr><td><a href="{% url \'commentaries:commentary\' ' + str(self.id) + ' %}">' + self.pub_title + '</a></td></tr>'
#        header += '<tr><td>by ' + self.author_list + '</td></tr><tr><td> (published ' + str(self.pub_date) + ')</td></tr></table></li>'
#        header = '<li><ul><li><a href="{% url \'commentaries:commentary\' ' + str(self.id) + ' %}">' + self.pub_title + '</a></li>'
#        header += '<li>by ' + self.author_list + '</li><li> (published ' + str(self.pub_date) + ')</li></ul></li>'
#        header = '<li><p><a href="{% url \'commentaries:commentary\' ' + str(self.id) + ' %}">' + self.pub_title + '</a></p>'
#        header += '<p>by ' + self.author_list + '</p><p> (published ' + str(self.pub_date) + ')</p></li>'
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/commentaries/commentary/' + str(self.id) + '">' + self.pub_title + '</a></p>'
        header += '<p>by ' + self.author_list + '</p><p> (published ' + str(self.pub_date) + ')</p></div>'
        header += '<div class="flex-whitebox0"><p>Latest activity: ' + self.latest_activity.strftime('%Y-%m-%d %H:%M') + '</p></div>'
        header += '</div></li>'
        #header = '<li>'
        #header += '<p><a href="{% url \'commentaries:commentary\' commentary_id=' + str(self.id) + ' %}">' + self.pub_title + '</a></p>'
        #header += '<p>by ' + self.author_list + '</p><p> (published ' + str(self.pub_date) + ')</p>'
        #header += '<p>Latest activity: ' + str(self.latest_activity) + '</p>'
        #header += '</li>'
        return header
