from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db import models
from django.contrib.auth.models import User

from .models import *

from scipost.models import Contributor
from scipost.models import SCIPOST_DISCIPLINES, TITLE_CHOICES
from journals.models import SCIPOST_JOURNALS_SUBMIT, SCIPOST_JOURNALS_DOMAINS, SCIPOST_JOURNALS_SPECIALIZATIONS
from journals.models import journals_submit_dict, journals_domains_dict, journals_spec_dict


###############
# Submissions:
###############

SUBMISSION_STATUS = (
    ('unassigned', 'Unassigned'),
    ('assigned', 'Assigned to a specialty editor (response pending)'),
    ('EICassigned', 'Editor-in-charge assigned, manuscript under review'),
    ('review_closed', 'Review period closed, editorial recommendation pending'),
    ('EIC_has_recommended', 'Editor-in-charge has provided recommendation'),
    ('put_to_EC_voting', 'Undergoing voting at the Editorial College'),
    ('EC_vote_completed', 'Editorial College voting rounded up'),
    ('decided', 'Publication decision taken'),
    )
submission_status_dict = dict(SUBMISSION_STATUS)

SUBMISSION_ACTION_REQUIRED = (
    ('assign_EIC', 'Editor-in-charge to be assigned'),
    ('Fellow_accepts_or_refuse_assignment', 'Fellow must accept or refuse assignment'),
    ('EIC_runs_refereeing_round', 'Editor-in-charge to run refereeing round (inviting referees)'),
    ('EIC_closes_refereeing_round', 'Editor-in-charge to close refereeing round'),
    ('EIC_invites_author_response', 'Editor-in-charge invites authors to complete their replies'),
    ('EIC_formulates_editorial_recommendation', 'Editor-in-charge to formulate editorial recommendation'),
    ('EC_ratification', 'Editorial College ratifies editorial recommendation'),
    ('Decision_to_authors', 'Editor-in-charge forwards decision to authors'),
    )


class Submission(models.Model):
    submitted_by = models.ForeignKey(Contributor)
    assigned = models.BooleanField(default=False)
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT, verbose_name="Journal to be submitted to")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS) # set by Editors
    open_for_reporting = models.BooleanField(default=True)
    reporting_deadline = models.DateTimeField(default=timezone.now)
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
        header += '<tr><td>As Contributors: </td><td>&nbsp;</td>'
        if self.authors.all():
            for auth in self.authors.all():
                header += '<td><a href="/contributor/' + str(auth.id) + '">' + auth.user.first_name + ' ' + auth.user.last_name + '</a></td>'
        else:
            header += '<td>(none claimed)</td>'
        header += '</tr>'
        header += '<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="' + self.arxiv_link + '" target="_blank">' + self.arxiv_link + '</a></td></tr>'
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

    def status_info_as_table (self):
        header = '<table>'
#        if self.assignment is not None:
#            header += '<tr><td>Editor in charge: </td><td>&nbsp;</td><td>' + str(self.assignment.to) + '</td></tr>'
#        header += '<tr><td>Assigned: </td><td>&nbsp;</td><td>' + str(self.assigned) + '</td></tr>'
        header += '<tr><td>Current status: </td><td>&nbsp;</td><td>' + submission_status_dict[self.status] + '</td></tr>'
        header += '</table>'
        return mark_safe(header)


######################
# Editorial workflow #
######################

ASSIGNMENT_BOOL = ((True, 'Accept'), (False, 'Decline'))
ASSIGNMENT_NULLBOOL = ((None, 'Response pending'), (True, 'Accept'), (False, 'Decline'))

ASSIGNMENT_REFUSAL_REASONS = (
    ('BUS', 'Too busy'),
    ('COI', 'Conflict of interest: coauthor in last 5 years'),
    ('CCC', 'Conflict of interest: close colleague'),
    ('NIR', 'Cannot give an impartial assessment'),
    ('NIE', 'Not interested enough'),
    ('DNP', 'SciPost should not even consider this paper'),
    )
assignment_refusal_reasons_dict = dict(ASSIGNMENT_REFUSAL_REASONS)

class EditorialAssignment(models.Model):
    submission = models.ForeignKey(Submission)
    to = models.ForeignKey(Contributor)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    completed = models.BooleanField(default=False)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS, blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_answered = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return (self.to.user.first_name + ' ' + self.to.user.last_name + ' to become EIC of ' + 
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', assigned on ' + self.date_created.strftime('%Y-%m-%d'))
    
    def header_as_li(self):
        header = '<li><div class="flex-container">'
        header += ('<div class="flex-whitebox0"><p><a href="/submission/' + str(self.submission.id) +
                   '" class="pubtitleli">' + self.submission.title + '</a></p>')
        header += ('<p>by ' + self.submission.author_list +
                   '</p><p> (submitted ' + str(self.submission.submission_date) +
                   ' to ' + journals_submit_dict[self.submission.submitted_to_journal] +
                   ')</p>')
        header += ('<p>Status: ' + submission_status_dict[self.submission.status] + 
                   '</p><p>Manage this Submission from its <a href="/submissions/editorial_page/' + str(self.submission.id) + '">Editorial Page</a>.</p>')
        header += '</div></div></li>'
        return mark_safe(header)


class RefereeInvitation(models.Model):
    submission = models.ForeignKey(Submission)
    referee = models.ForeignKey(Contributor, related_name='referee', blank=True, null=True)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    email_address = models.EmailField()
    invitation_key = models.CharField(max_length=40, default='') # if Contributor not found, person is invited to register
    date_invited = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey(Contributor, related_name='referee_invited_by', blank=True, null=True)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    date_responded = models.DateTimeField(blank=True, null=True)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS, blank=True, null=True)
    fulfilled = models.BooleanField(default=False) # True if a Report has been submitted

    def __str__(self):
        return (self.first_name + ' ' + self.last_name + ' to referee ' + 
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', invited on ' + self.date_invited.strftime('%Y-%m-%d'))
    
    def summary_as_li(self):
        output = '<li>' + self.first_name + ' ' + self.last_name + ', '
        output += 'invited ' + self.date_invited.strftime('%Y-%m-%d %H:%M') + ', '
        if self.accepted is not None:
            if self.accepted:
                output += 'accepted '
            else:
                output += 'declined ' 
            output += self.date_responded.strftime('%Y-%m-%d %H:%M')
        else:
            output += 'response pending'
        output += '; task fulfilled: '
        if self.fulfilled:
            output += 'True'
        else:
            output += 'False'
        return mark_safe(output)
    

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
quality_spec_dict = dict(QUALITY_SPEC)


RANKING_CHOICES = (
    (101, '-'), # Only values between 0 and 100 are kept, anything outside those limits is discarded.
    (100, 'top'), (80, 'high'), (60, 'good'), (40, 'ok'), (20, 'low'), (0, 'poor')
    )
ranking_choices_dict = dict(RANKING_CHOICES)

REPORT_REC = (
    (1, 'Publish as Tier I (top 10% of papers in this journal)'),
    (2, 'Publish as Tier II (top 50% of papers in this journal)'),
    (3, 'Publish as Tier III (meets the criteria of this journal)'),
    (-1, 'Ask for minor revision'),
    (-2, 'Ask for major revision'),
    (-3, 'Reject')
    )
report_rec_dict = dict(REPORT_REC)

class Report(models.Model):    
    """ Both types of reports, invited or contributed. """
    # status:
    # 1: vetted
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    status = models.SmallIntegerField(default=0)
    submission = models.ForeignKey(Submission)
#    date_invited = models.DateTimeField('date invited', blank=True, null=True)
#    invited_by = models.ForeignKey(Contributor, blank=True, null=True, related_name='invited_by')
    invited = models.BooleanField(default=False) # filled from RefereeInvitation objects at moment of report submission
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
    formatting = models.SmallIntegerField(choices=QUALITY_SPEC, verbose_name="Quality of paper formatting")
    grammar = models.SmallIntegerField(choices=QUALITY_SPEC, verbose_name="Quality of English grammar")
    # 
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    remarks_for_editors = models.TextField(default='', blank=True, verbose_name='optional remarks for the Editors only')
    anonymous = models.BooleanField(default=True, verbose_name='Publish anonymously')


    def print_identifier(self):
        output = '<div class="reportid">\n'
        output += '<h3><a id="report_id' + str(self.id) + '"></a>'
        if self.anonymous:
            output += 'Anonymous Report ' + str(self.id)
        else:
            output += ('<a href="/contributor/' + str(self.author.id) + '">' +
                       self.author.user.first_name + ' ' + self.author.user.last_name + '</a>')
        output += ' on ' + self.date_submitted.strftime("%Y-%m-%d")
        output += '</h3></div>'
        return mark_safe(output)
    
    def print_contents(self):
        output = ('<div class="row"><div class="col-2"><p>Strengths:</p></div><div class="col-10"><p>' +
                  self.strengths + '</p></div></div>' + 
                  '<div class="row"><div class="col-2"><p>Weaknesses:</p></div><div class="col-10"><p>' +
                  self.weaknesses + '</p></div></div>' +
                  '<div class="row"><div class="col-2"><p>Report:</p></div><div class="col-10"><p>' +
                  self.report + '</p></div></div>' +
                  '<div class="row"><div class="col-2"><p>Requested changes:</p></div><div class="col-10"><p>' +
                  self.requested_changes + '</p></div></div>')
        output += '<div class="reportRatings"><ul>'
        output += '<li>validity: ' + ranking_choices_dict[self.validity] + '</li>'
        output += '<li>significance: ' + ranking_choices_dict[self.significance] + '</li>'
        output += '<li>originality: ' + ranking_choices_dict[self.originality] + '</li>'
        output += '<li>clarity: ' + ranking_choices_dict[self.clarity] + '</li>'
        output += '<li>formatting: ' + quality_spec_dict[self.formatting] + '</li>'
        output += '<li>grammar: ' + quality_spec_dict[self.grammar] + '</li>'
        output += '</ul></div>'
        return mark_safe(output)
                  
    def print_contents_for_editors(self):
        output = ('<div class="row"><div class="col-2">Qualification:</p></div><div class="col-10"><p>' + 
                  ref_qualif_dict[self.qualification] + '</p></div></div>')
        output += self.print_contents()
        output += '<h3>Recommendation: ' + report_rec_dict[self.recommendation] + '</h3>'
        return mark_safe(output)
