from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from contributors.models import Contributor

COMMENTARY_TYPES = (
    ('published', 'published paper'),
    ('preprint', 'arXiv preprint (from at least 4 weeks ago)'),
    )

class Commentary(models.Model):
    """ A Commentary contains all the contents of a SciPost Commentary page for a given publication. """
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey (Contributor, blank=True, null=True)
    type = models.CharField(max_length=9) # published paper or arxiv preprint
    open_for_commenting = models.BooleanField(default=True)
    pub_title = models.CharField(max_length=300)
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')
    pub_DOI_link = models.URLField(verbose_name='DOI link to the original publication')
    author_list = models.CharField(max_length=1000)
    pub_date = models.DateField(verbose_name='date of original publication')
    pub_abstract = models.TextField()
    nr_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    correctness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    usefulness_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0)
    latest_activity = models.DateTimeField(default=timezone.now)

    def __str__ (self):
        return self.pub_title

