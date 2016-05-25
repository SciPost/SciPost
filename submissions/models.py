from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.template import Template, Context

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
#    ('EICrequested', 'A request to become EIC has been sent to a specialty editor (response pending)'),
    ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'),
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
#    ('Fellow_accepts_or_refuse_assignment', 'Fellow must accept or refuse assignment'),
    ('EIC_runs_refereeing_round', 'Editor-in-charge to run refereeing round (inviting referees)'),
    ('EIC_closes_refereeing_round', 'Editor-in-charge to close refereeing round'),
    ('EIC_invites_author_response', 'Editor-in-charge invites authors to complete their replies'),
    ('EIC_formulates_editorial_recommendation', 'Editor-in-charge to formulate editorial recommendation'),
    ('EC_ratification', 'Editorial College ratifies editorial recommendation'),
    ('Decision_to_authors', 'Editor-in-charge forwards decision to authors'),
    )


class Submission(models.Model):
    submitted_by = models.ForeignKey(Contributor)
    editor_in_charge = models.ForeignKey(Contributor, related_name='EIC', blank=True, null=True)
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT, verbose_name="Journal to be submitted to")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    specialization = models.CharField(max_length=1, choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS) # set by Editors
    referees_flagged = models.TextField(blank=True, null=True)
    open_for_reporting = models.BooleanField(default=False)
    reporting_deadline = models.DateTimeField(default=timezone.now)
    open_for_commenting = models.BooleanField(default=False)
    title = models.CharField(max_length=300)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub')
    authors_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub_claims')
    authors_false_claims = models.ManyToManyField (Contributor, blank=True, related_name='authors_sub_false_claims')
    abstract = models.TextField()
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')
    metadata = JSONField(default={}, blank=True, null=True)
    submission_date = models.DateField(verbose_name='submission date')
    latest_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        permissions = (
            ('can_take_editorial_actions', 'Can take editorial actions'),
            )
    
    def __str__ (self):
        return self.title[:30] + ' by ' + self.author_list[:30]

    @property
    def reporting_deadline_has_passed(self):
        if timezone.now() > self.reporting_deadline:
            return True
        return False


    def header_as_table (self):
        # for Submission page
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>{{ author_list }}</td></tr>'
        header += '<tr><td>As Contributors: </td><td>&nbsp;</td>'
        if self.authors.all():
            header += '<td>'
            for auth in self.authors.all():
                header += '<a href="/contributor/' + str(auth.id) + '">' + auth.user.first_name + ' ' + auth.user.last_name + '</a>&nbsp;&nbsp;'
            header += '</td>'
        else:
            header += '<td>(none claimed)</td>'
        header += '</tr>'
        header += '<tr><td>arxiv Link: </td><td>&nbsp;</td><td><a href="{{ arxiv_link }}" target="_blank">{{ arxiv_link }}</a></td></tr>'
        header += '<tr><td>Date submitted: </td><td>&nbsp;</td><td>{{ submission_date }}</td></tr>'
        header += '<tr><td>Submitted by: </td><td>&nbsp;</td><td>{{ submitted_by }}</td></tr>'
        header += '<tr><td>Submitted to: </td><td>&nbsp;</td><td>{{ to_journal }}</td></tr>'
        header += '<tr><td>Domain(s): </td><td>&nbsp;</td><td>{{ domain }}</td></tr>'
        header += '<tr><td>Specialization: </td><td>&nbsp;</td><td>{{ spec }}</td></tr>'
        header += '</table>'
        template = Template(header)
        context = Context({'title': self.title, 'author_list': self.author_list,
                           'arxiv_link': self.arxiv_link, 'submission_date': self.submission_date,
                           'submitted_by': self.submitted_by, 'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'domain': journals_domains_dict[self.domain], 'spec': journals_spec_dict[self.specialization]})
        return template.render(context)


    def header_as_li (self):
        # for search lists
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/submission/{{ id }}" class="pubtitleli">{{ title }}</a></p>'
        header += ('<p>by {{ author_list }}</p><p> (submitted {{ submission_date }} to {{ to_journal }})' +
                   ' - latest activity: {{ latest_activity }}</p>'
                   '</div></div></li>')
        context = Context({'id': self.id, 'title': self.title, 'author_list': self.author_list,
                           'submission_date': self.submission_date, 
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M')})
        template = Template(header)
        return template.render(context)


    def header_as_li_for_authors (self):
        # for search lists
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/submission/{{ id }}" class="pubtitleli">{{ title }}</a></p>'
        header += ('<p>by {{ author_list }}</p><p> (submitted {{ submission_date }} to {{ to_journal }})' +
                   ' - latest activity: {{ latest_activity }}</p>'
                   '<p>Status: {{ status }}</p></div></div></li>')
        context = Context({'id': self.id, 'title': self.title, 'author_list': self.author_list,
                           'submission_date': self.submission_date, 
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M'),
                           'status': submission_status_dict[self.status]})
        template = Template(header)
        return template.render(context)


    def header_as_li_for_Fellows (self):
        # for submissions pool
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/submission/{{ id }}" class="pubtitleli">{{ title }}</a></p>'
        header += ('<p>by {{ author_list }}</p><p> (submitted {{ submission_date }} to {{ to_journal }})'
                   ' - latest activity: {{ latest_activity }}</p>')
        if self.status == 'unassigned':
            header += ('<p style="color: red">Status: {{ status }}.'
                       ' You can volunteer to become Editor-in-charge by <a href="/submissions/volunteer_as_EIC/{{ id }}">clicking here</a>.</p>')
        else:
            header += '<p>Editor-in-charge: {{ EIC }}</p><p>Status: {{ status }}</p>'
        nr_ref_invited = RefereeInvitation.objects.filter(submission=self).count()
        nr_invited_reports_in = Report.objects.filter(submission=self, status=1, invited=True).count()
        nr_contrib_reports_in = Report.objects.filter(submission=self, status=1, invited=False).count()
        nr_reports_awaiting_vetting = Report.objects.filter(submission=self, status=0).count()
        nr_reports_refused = Report.objects.filter(submission=self, status__lte=-1).count()
        header += ('<p>Nr referees invited: ' + str(nr_ref_invited) + ', nr reports obtained: ' +
                   str(nr_invited_reports_in + nr_contrib_reports_in) + ' [' +
                   str(nr_invited_reports_in) + ' invited/ ' + str(nr_contrib_reports_in) +
                   ' contributed], nr refused: ' + str(nr_reports_refused) +
                   ', nr awaiting vetting: ' + str(nr_reports_awaiting_vetting) )
        header += '</div></div></li>'
        context = Context({'id': self.id, 'title': self.title, 'author_list': self.author_list,
                           'submission_date': self.submission_date, 
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M'),
                           'EIC': str(self.editor_in_charge),
                           'status': submission_status_dict[self.status]})
        template = Template(header)
        return template.render(context)
    

    def simple_header_as_li (self):
        # for Lists
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/submission/{{ id }}" class="pubtitleli">{{ title }}</a></p>'
        header += '<p>by {{ author_list }}</p></div></div></li>'
        context = Context({'id': self.id, 'title': self.title, 'author_list': self.author_list})
        template = Template(header)
        return template.render(context)


    def status_info_as_table (self):
        header = '<table>'
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
    deprecated = models.BooleanField(default=False) # becomes True if another Fellow becomes Editor-in-charge
    completed = models.BooleanField(default=False)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS, blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_answered = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return (self.to.user.first_name + ' ' + self.to.user.last_name + ' to become EIC of ' + 
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', requested on ' + self.date_created.strftime('%Y-%m-%d'))

    def info_as_li(self):
        context = Context({'first_name': self.to.user.first_name,
                           'last_name': self.to.user.last_name,
                           'date_created': self.date_created.strftime('%Y-%m-%d %H:%M')})
        info = '<li'
        if self.accepted:
            info += ' style="color: green"'
        elif self.deprecated:
            info += ' style="color: purple"'
        elif self.accepted == False:
            if self.refusal_reason == 'NIE' or self.refusal_reason == 'DNP':
                info += ' style="color: #CC0000"'
            else:
                info += ' style="color: #FF7700"'
        info += '>{{ first_name }} {{ last_name }}, requested {{ date_created }}'
        if self.accepted:
            info += ', accepted {{ date_answered }}'
            context['date_answered'] = self.date_answered.strftime('%Y-%m-%d %H:%M')
        if self.deprecated:
            info += ', deprecated'
        if self.refusal_reason:
            info += ', declined {{ date_answered }}, reason: {{ reason }}'
            context['date_answered'] = self.date_answered.strftime('%Y-%m-%d %H:%M')
            context['reason'] = assignment_refusal_reasons_dict[self.refusal_reason]
        info += '</li>'
        template = Template(info)
        return template.render(context)
        
    def header_as_li(self):
        header = '<li><div class="flex-container">'
        header += '<div class="flex-whitebox0"><p><a href="/submission/{{ id }}" class="pubtitleli">{{ title }}</a></p>'
        header += '<p>by {{ author_list }}</p><p> (submitted {{ date }} to {{ to_journal }})</p>'
        header += '<p>Status: {{ status }}</p><p>Manage this Submission from its '
        header += '<a href="/submissions/editorial_page/{{ id }}">Editorial Page</a>.</p></div></div></li>'
        template = Template(header)
        context = Context({'id': self.submission.id, 'title': self.submission.title,
                   'author_list': self.submission.author_list, 'date': self.submission.submission_date,
                   'to_journal': journals_submit_dict[self.submission.submitted_to_journal],
                   'status': submission_status_dict[self.submission.status]})
        return template.render(context)


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
        context = Context({'first_name': self.first_name, 'last_name': self.last_name,
                           'date_invited': self.date_invited.strftime('%Y-%m-%d %H:%M')})
        output = '<li>{{ first_name }} {{ last_name }}, invited {{ date_invited }}, '
        if self.accepted is not None:
            if self.accepted:
                output += '<strong style="color: green">task accepted</strong> '
            else:
                output += '<strong style="color: red">task declined</strong> ' 
            output += '{{ date_responded }}'
            context['date_responded'] = self.date_responded.strftime('%Y-%m-%d %H:%M')
        else:
            output += 'response pending'
        if self.fulfilled:
            output += '; Report has been delivered'

        template = Template(output)
        return template.render(context)
    

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
    # status: see forms.py:REPORT_REFUSAL_CHOICES
    # 1: vetted
    # 0: unvetted
    # -1: rejected (unclear)
    # -2: rejected (incorrect)
    # -3: rejected (not useful)
    # -4: rejected (not academic in style)
    status = models.SmallIntegerField(default=0)
    submission = models.ForeignKey(Submission)
    invited = models.BooleanField(default=False) # filled from RefereeInvitation objects at moment of report submission
    flagged = models.BooleanField(default=False) # if author of report has been flagged by submission authors (surname check only)
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


    def __str__(self):
        return (self.author.user.first_name + ' ' + self.author.user.last_name + ' on ' +
                self.submission.title[:50] + ' by ' + self.submission.author_list[:50])

    def print_identifier(self):
        context = Context({'id': self.id, 'author_id': self.author.id,
                           'first_name': self.author.user.first_name,
                           'last_name': self.author.user.last_name,
                           'date_submitted': self.date_submitted.strftime("%Y-%m-%d")})
        output = '<div class="reportid">\n'
        output += '<h3><a id="report_id{{ id }}"></a>'
        if self.anonymous:
            output += 'Anonymous Report {{ id }}'
        else:
            output += '<a href="/contributor/{{ author_id }}">{{ first_name }} {{ last_name }}</a>'
        output += ' on {{ date_submitted }}</h3></div>'
        template = Template(output)
        return template.render(context)

    
    def print_contents(self):
        context = Context({'strengths': self.strengths, 'weaknesses': self.weaknesses,
                           'report': self.report, 'requested_changes': self.requested_changes})
        output = ('<div class="row"><div class="col-2"><p>Strengths:</p></div><div class="col-10"><p>{{ strengths }}</p></div></div>' + 
                  '<div class="row"><div class="col-2"><p>Weaknesses:</p></div><div class="col-10"><p>{{ weaknesses }}</p></div></div>' +
                  '<div class="row"><div class="col-2"><p>Report:</p></div><div class="col-10"><p>{{ report }}</p></div></div>' +
                  '<div class="row"><div class="col-2"><p>Requested changes:</p></div><div class="col-10"><p>{{ requested_changes }}</p></div></div>')
        output += '<div class="reportRatings"><ul>'
        output += '<li>validity: ' + ranking_choices_dict[self.validity] + '</li>'
        output += '<li>significance: ' + ranking_choices_dict[self.significance] + '</li>'
        output += '<li>originality: ' + ranking_choices_dict[self.originality] + '</li>'
        output += '<li>clarity: ' + ranking_choices_dict[self.clarity] + '</li>'
        output += '<li>formatting: ' + quality_spec_dict[self.formatting] + '</li>'
        output += '<li>grammar: ' + quality_spec_dict[self.grammar] + '</li>'
        output += '</ul></div>'
        template = Template(output)
        return template.render(context)
    
                  
    def print_contents_for_editors(self):
        context = Context({'id': self.id, 'author_id': self.author.id,
                           'author_first_name': self.author.user.first_name,
                           'author_last_name': self.author.user.last_name,
                           'date_submitted': self.date_submitted.strftime("%Y-%m-%d")})
        output = '<div class="reportid">\n'
        output += '<h3><a id="report_id{{ id }}"></a>'
        if self.anonymous:
            output += '(chose public anonymity) '
        output += '<a href="/contributor/{{ author_id }}">{{ author_first_name }} {{ author_last_name }}</a>'
        output += ' on {{ date_submitted }}</h3></div>'
        output += ('<div class="row"><div class="col-2">Qualification:</p></div><div class="col-10"><p>' + 
                  ref_qualif_dict[self.qualification] + '</p></div></div>')
        output += self.print_contents()
        output += '<h3>Recommendation: ' + report_rec_dict[self.recommendation] + '</h3>'
        template = Template(output)
        return template.render(context)


##########################
# EditorialCommunication #
##########################

ED_CORR_CHOICES = (
    ('EtoA', 'Editor-in-charge to Author'),
    ('AtoE', 'Author to Editor-in-charge'),
    ('EtoR', 'Editor-in-charge to Referee'),
    ('RtoE', 'Referee to Editor-in-Charge'),
    ('EtoS', 'Editor-in-charge to SciPost Editorial Administration'),
    ('StoE', 'SciPost Editorial Administration to Editor-in-charge'),
    )
ed_corr_choices_dict = dict(ED_CORR_CHOICES)

class EditorialCommunication(models.Model):
    """ 
    Each individual communication between Editor-in-charge 
    to and from Referees and Authors becomes an instance of this class.
    """
    submission = models.ForeignKey(Submission)
    referee = models.ForeignKey(Contributor, related_name='referee_in_correspondence', blank=True, null=True)
    comtype = models.CharField(max_length=4, choices=ED_CORR_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

    def __str__ (self):
        output = self.comtype 
        if self.referee is not None:
            output += ' ' + self.referee.user.first_name + ' ' + self.referee.user.last_name
        output += ' for submission ' + self.submission.title[:30] + ' by ' + self.submission.author_list[:30]
        return output

    def print_contents_as_li(self):
        context = Context({'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M"), 'text': self.text})
        output = '<li><p>'
        if self.comtype == 'EtoA':
            output += 'From you to Authors'
        elif self.comtype == 'EtoR':
            output += 'From you to Referee '
            try:
                output += self.referee.user.first_name + ' ' + self.referee.user.last_name
            except AttributeError:
                pass
        elif self.comtype == 'EtoS':
            output += 'From you to SciPost Ed Admin'
        elif self.comtype == 'AtoE':
            output += 'From Authors to you'
        elif self.comtype == 'RtoE':
            output += 'From Referee '
            try:
                output += self.referee.user.first_name + ' ' + self.referee.user.last_name + ' to you'
            except AttributeError:
                pass
        elif self.comtype == 'StoE':
            output += 'From SciPost Ed Admin to you'
        output += ' on {{ timestamp }}</p><p>{{ text }}</p>'
        template = Template(output)
        return template.render(context)



############################
# Editorial Recommendation #
############################

# From the Editor-in-charge of a Submission
class EICRecommendation(models.Model):
    submission = models.ForeignKey(Submission)
    date_submitted = models.DateTimeField('date submitted')
    remarks_for_authors = models.TextField(blank=True, null=True)
    requested_changes = models.TextField(verbose_name="requested changes", blank=True, null=True)
    remarks_for_editorial_college = models.TextField(default='', blank=True, null=True, verbose_name='optional remarks for the Editorial College')
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    # Editorial Fellows who have assessed this recommendation:
    voted_for = models.ManyToManyField (Contributor, blank=True, related_name='voted_for')
    voted_against = models.ManyToManyField (Contributor, blank=True, related_name='voted_against')
    voting_deadline = models.DateTimeField('date submitted', default=timezone.now)
 
    @property
    def nr_for(self):
        return self.voted_for.count()
        
    @property
    def nr_against(self):
        return self.voted_against.count()
