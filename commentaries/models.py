from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from scipost.models import Contributor

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

