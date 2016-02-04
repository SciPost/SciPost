from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from journals.models import *
from scipost.models import *

THESIS_TYPES = (
    ('MA', 'Master\'s'),
    ('PhD', 'Ph.D.'),
    )
theses_type_dict = dict(THESIS_TYPES)


class ThesisLink(models.Model):
    """ An URL pointing to a thesis """
    requested_by = models.ForeignKey (Contributor, blank=True, null=True, related_name='thesislink_requested_by')
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey (Contributor, blank=True, null=True)
    type = models.CharField(max_length=3, choices=THESIS_TYPES)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS, default='E')
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS, default='A')
    open_for_commenting = models.BooleanField(default=True)
    title = models.CharField(max_length=300, verbose_name='title')
    pub_link = models.URLField(verbose_name='URL (external repository)')
    author = models.CharField(max_length=1000)
    author_as_cont = models.ManyToManyField (Contributor, blank=True, related_name='author_cont')
    institution = models.CharField(max_length=300, verbose_name='degree granting institution')
    defense_date = models.DateField(verbose_name='date of thesis defense')
    abstract = models.TextField(verbose_name='abstract')

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
        return self.title

    def header_as_table (self):
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>' + self.title + '</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>' + self.author + '</td></tr>'
        header += '<tr><td>URL: </td><td>&nbsp;</td><td><a href="' + self.pub_link + '">' + self.pub_link + '</a></td></tr>'
        header += '<tr><td>Degree granting institution: </td><td>&nbsp;</td><td>' + self.institution + '</td></tr>'
        header += '<tr><td>Defense date: </td><td>&nbsp;</td><td>' + str(self.defense_date) + '</td></tr>'
        header += '</table>'
        return header

    def header_as_li (self):
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/theses/thesis/' + str(self.id) + '">' + self.title + '</a></p>'
        header += '<p>by ' + self.author + '</p><p> (published ' + str(self.defense_date) + ')</p></div>'
        header += '<div class="flex-whitebox0"><p>Latest activity: ' + self.latest_activity.strftime('%Y-%m-%d %H:%M') + '</p></div>'
        header += '</div></li>'
        return header
