from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from scipost.models import Contributor
from journals.models import *



###############
# Submissions:
###############

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
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT)
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    status = models.SmallIntegerField(choices=SUBMISSION_STATUS) # set by Editors
    open_for_reporting = models.BooleanField(default=True)
    open_for_commenting = models.BooleanField(default=True)
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub')
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


###########
# Reports:
###########

REPORT_REC = (
    (1, 'Publish as Tier I (top 10% of papers in this journal)'),
    (2, 'Publish as Tier II (top 50% of papers in this journal)'),
    (3, 'Publish as Tier III (meets the criteria of this journal)'),
    (-1, 'Ask for minor revision'),
    (-2, 'Ask for major revision'),
    (-3, 'Reject')
    )

class Report(models.Model):    
    """ Both types of reports, invited or contributed. """
    # status:
    # 1: vetted (by Contributor with rank >= 2) 
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    status = models.SmallIntegerField(default=0)
    submission = models.ForeignKey(Submission)
    author = models.ForeignKey(Contributor)
    qualification = models.PositiveSmallIntegerField(default=0)
    strengths = models.TextField()
    weaknesses = models.TextField()
    report = models.TextField()
    requested_changes = models.TextField(verbose_name="requested changes")
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    date_invited = models.DateTimeField('date invited', blank=True, null=True)
    invited_by = models.ForeignKey(Contributor, blank=True, null=True, related_name='invited_by')
    date_submitted = models.DateTimeField('date submitted')
    # Aggregates of ratings applied to this report:
    nr_relevance_ratings = models.IntegerField(default=0)
    relevance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_importance_ratings = models.IntegerField(default=0)
    importance_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_clarity_ratings = models.IntegerField(default=0)
    clarity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_validity_ratings = models.IntegerField(default=0)
    validity_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    nr_rigour_ratings = models.IntegerField(default=0)
    rigour_rating = models.DecimalField(default=0, max_digits=3, decimal_places=0, null=True)
    
