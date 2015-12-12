from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from contributors.models import Contributor
from journals.models import *


SUBMISSION_STATUS = (
    (0, 'unassigned'),
    (1, 'editor in charge assigned'),
    (2, 'under review'),
    (3, 'reviewed, peer checking period'),
    (4, 'reviewed, peer checked, editorial decision pending'),
    (5, 'editorial decision'),
    )


class Submission(models.Model):
    submitted_by = models.ForeignKey(Contributor)
    vetted = models.BooleanField(default=False)
    editor_in_charge = models.ForeignKey(Contributor, related_name="editor_in_charge", blank=True, null=True) # assigned by Journal Editor
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS)
    domain = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_DOMAINS, default='E')
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    status = models.SmallIntegerField(choices=SUBMISSION_STATUS) # set by Editors
    open_for_reporting = models.BooleanField(default=True)
    open_for_commenting = models.BooleanField(default=True)
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000)
    abstract = models.TextField()
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')
    submission_date = models.DateField(verbose_name='date of original publication')

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

