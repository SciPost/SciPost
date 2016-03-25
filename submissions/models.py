from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from .models import *

from scipost.models import *
from journals.models import *



###############
# Submissions:
###############

SUBMISSION_STATUS = (
    ('unassigned', 'unassigned'),
    ('forwarded', 'forwarded to a specialty editor'),
    ('SEICassigned', 'specialty editor-in-charge assigned'),
    ('under_review', 'under review'),
    ('review_completed', 'review period closed, editorial recommendation pending'),
    ('SEIC_has_recommended', 'specialty editor-in-charge has provided recommendation'),
    ('decided', 'journal editor-in-chief has fixed decision'),
    )
submission_status_dict = dict(SUBMISSION_STATUS)

class Submission(models.Model):
    submitted_by = models.ForeignKey(Contributor)
    vetted = models.BooleanField(default=False)
    editor_in_charge = models.ForeignKey(Contributor, related_name="editor_in_charge", blank=True, null=True) # assigned by Journal Editor
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT, verbose_name="Journal to be submitted to")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS) # set by Editors
    open_for_reporting = models.BooleanField(default=True)
    open_for_commenting = models.BooleanField(default=True)
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub')
    authors_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub_claims')
    authors_false_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub_false_claims')
    abstract = models.TextField()
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')
    submission_date = models.DateField(verbose_name='submission date')
    latest_activity = models.DateTimeField(default=timezone.now)

    def __str__ (self):
        return self.title

    def header_as_table (self):
        # for Submission page
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>' + self.title + '</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>' + self.author_list + '</td></tr>'
        header += '<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="' + self.arxiv_link + '">' + self.arxiv_link + '</a></td></tr>'
        header += '<tr><td>Date submitted: </td><td>&nbsp;</td><td>' + str(self.submission_date) + '</td></tr>'
        header += '<tr><td>Submitted by: </td><td>&nbsp;</td><td>' + str(self.submitted_by) + '</td></tr>'
        header += '<tr><td>Submitted to: </td><td>&nbsp;</td><td>' + journals_submit_dict[self.submitted_to_journal] + '</td></tr>'
        header += '<tr><td>Domain(s): </td><td>&nbsp;</td><td>' + journals_domains_dict[self.domain] + '</td></tr>'
        header += '<tr><td>Specialization: </td><td>&nbsp;</td><td>' + journals_spec_dict[self.specialization] + '</td></tr>'
        header += '</table>'
        return header

    def header_as_li (self):
        # for search lists
        header = '<li><div class="flex-container">'
        header += ('<div class="flex-whitebox0"><p><a href="/submission/' + str(self.id) + 
                   '" class="pubtitleli">' + self.title + '</a></p>')
        header += ('<p>by ' + self.author_list + 
                   '</p><p> (submitted ' + str(self.submission_date) + 
                   ' to ' + journals_submit_dict[self.submitted_to_journal] + 
                   ') - latest activity: ' + self.latest_activity.strftime('%Y-%m-%d %H:%M') + 
                   '</p></div>')
        header += '</div></li>'
        return header


    def submission_info_as_table (self):
        header = '<table>'
        header += '<tr><td>Editor in charge: </td><td>&nbsp;</td><td>' + str(self.editor_in_charge) + '</td></tr>'
        header += '<tr><td>Vetted: </td><td>&nbsp;</td><td>' + str(self.vetted) + '</td></tr>'
        header += '<tr><td>Status: </td><td>&nbsp;</td><td>' + submission_status_dict[self.status] + '</td></tr>'
        header += '</table>'
        return header

###########
# Reports:
###########

REFEREE_QUALIFICATION = (
    (4, 'expert in this subject'),
    (3, 'very knowledgeable in this subject'),
    (2, 'knowledgeable in this subject'),
    (1, 'generally qualified'),
    (0, 'not qualified'),
    )
ref_qualif_dict = dict(REFEREE_QUALIFICATION)

QUALITY_SPEC = (
    (6, 'perfect'),
    (5, 'excellent'),
    (4, 'good'),
    (3, 'reasonable'),
    (2, 'acceptable'),
    (1, 'below threshold'),
    (0, 'mediocre'),
    )

RANKING_CHOICES = (
    (101, '-'), # Only values between 0 and 100 are kept, anything outside those limits is discarded.
    (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')
    )

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
    date_invited = models.DateTimeField('date invited', blank=True, null=True)
    invited_by = models.ForeignKey(Contributor, blank=True, null=True, related_name='invited_by')
    date_submitted = models.DateTimeField('date submitted')
    author = models.ForeignKey(Contributor)
    qualification = models.PositiveSmallIntegerField(choices=REFEREE_QUALIFICATION, verbose_name="Qualification to referee this: I am ")
    # Text-based reporting
    strengths = models.TextField()
    weaknesses = models.TextField()
    report = models.TextField()
    requested_changes = models.TextField(verbose_name="requested changes")
    # Qualities:
    validity = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    significance = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    originality = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    clarity = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    formatting = models.SmallIntegerField(choices=QUALITY_SPEC, blank=True, verbose_name="Quality of paper formatting")
    grammar = models.SmallIntegerField(choices=QUALITY_SPEC, blank=True, verbose_name="Quality of English grammar")
    # 
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    anonymous = models.BooleanField(default=True, verbose_name='Publish anonymously')
