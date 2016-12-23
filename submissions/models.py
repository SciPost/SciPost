import datetime

from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db import models, transaction
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.template import Template, Context

from .models import *

from scipost.models import ChoiceArrayField, Contributor, title_dict, Remark
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS, subject_areas_dict
from scipost.models import TITLE_CHOICES
from journals.models import SCIPOST_JOURNALS_SUBMIT, SCIPOST_JOURNALS_DOMAINS
from journals.models import SCIPOST_JOURNALS_SPECIALIZATIONS
from journals.models import journals_submit_dict, journals_domains_dict, journals_spec_dict
from journals.models import Publication


###############
# Submissions:
###############

SUBMISSION_STATUS = (
    ('unassigned', 'Unassigned, undergoing pre-screening'),
    ('assignment_failed', 'Failed to assign Editor-in-charge; manuscript rejected'),
    ('EICassigned', 'Editor-in-charge assigned, manuscript under review'),
    ('review_closed', 'Review period closed, editorial recommendation pending'),
    # If revisions required: resubmission creates a new Submission object
    ('revision_requested', 'Editor-in-charge has requested revision'),
    ('resubmitted', 'Has been resubmitted'),
    # If acceptance/rejection:
    ('voting_in_preparation', 'Voting in preparation (eligible Fellows being selected)'),
    ('put_to_EC_voting', 'Undergoing voting at the Editorial College'),
    ('EC_vote_completed', 'Editorial College voting rounded up'),
    ('accepted', 'Publication decision taken: accept'),
    ('rejected', 'Publication decision taken: reject'),
    ('rejected_visible', 'Publication decision taken: reject (still publicly visible)'),
    ('published', 'Published'),
    # If withdrawn:
    ('withdrawn', 'Withdrawn by the Authors'),
    )
submission_status_dict = dict(SUBMISSION_STATUS)

SUBMISSION_STATUS_OUT_OF_POOL = [
    'assignment_failed',
    'resubmitted',
    'published',
    'withdrawn',
]

SUBMISSION_STATUS_PUBLICLY_UNLISTED = [
    'unassigned',
    'assignment_failed',
    'resubmitted',
    'rejected',
    'published',
    'withdrawn',
]

SUBMISSION_TYPE = (
    ('Letter', 'Letter (broad-interest breakthrough results)'),
    ('Article', 'Article (in-depth reports on specialized research)'),
    ('Review', 'Review (candid snapshot of current research in a given area)'),
)
submission_type_dict = dict(SUBMISSION_TYPE)


class Submission(models.Model):
    # Main submission fields
    author_comments = models.TextField(blank=True, null=True)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    editor_in_charge = models.ForeignKey(Contributor, related_name='EIC', blank=True, null=True,
                                         on_delete=models.CASCADE)
    is_current = models.BooleanField(default=True)
    is_resubmission = models.BooleanField(default=False)
    list_of_changes = models.TextField(blank=True, null=True)
    open_for_commenting = models.BooleanField(default=False)
    open_for_reporting = models.BooleanField(default=False)
    referees_flagged = models.TextField(blank=True, null=True)
    referees_suggested = models.TextField(blank=True, null=True)
    remarks_for_editors = models.TextField(blank=True, null=True)
    reporting_deadline = models.DateTimeField(default=timezone.now)
    secondary_areas = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS, default='unassigned')  # set by Editors
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE,
                                       blank=True, null=True, default=None)
    submitted_by = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT,
                                            verbose_name="Journal to be submitted to")
    title = models.CharField(max_length=300)

    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField(Contributor, blank=True, related_name='authors_sub')
    authors_claims = models.ManyToManyField(Contributor, blank=True,
                                            related_name='authors_sub_claims')
    authors_false_claims = models.ManyToManyField(Contributor, blank=True,
                                                  related_name='authors_sub_false_claims')
    abstract = models.TextField()

    # Arxiv identifiers with/without version number
    arxiv_identifier_w_vn_nr = models.CharField(max_length=15, default='0000.00000v0')
    arxiv_identifier_wo_vn_nr = models.CharField(max_length=10, default='0000.00000')
    arxiv_vn_nr = models.PositiveSmallIntegerField(default=1)
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')

    # Metadata
    metadata = JSONField(default={}, blank=True, null=True)
    submission_date = models.DateField(verbose_name='submission date', default=timezone.now)
    latest_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        permissions = (
            ('can_take_editorial_actions', 'Can take editorial actions'),
            )

    def __str__(self):
        header = (self.arxiv_identifier_w_vn_nr + ', '
                  + self.title[:30] + ' by ' + self.author_list[:30])
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version ' + str(self.arxiv_vn_nr) + ')'
        try:
            header += ' (published as ' + self.publication.citation() + ')'
        except Publication.DoesNotExist:
            pass
        return header

    @property
    def reporting_deadline_has_passed(self):
        if timezone.now() > self.reporting_deadline:
            return True
        return False

    @transaction.atomic
    def finish_submission(self):
        if self.is_resubmission:
            self.mark_other_versions_as_deprecated()
            self.copy_authors_from_previous_version()
            self.copy_EIC_from_previous_version()
            self.set_resubmission_defaults()
        else:
            self.authors.add(self.submitted_by)

        self.save()

    def make_assignment(self):
        assignment = EditorialAssignment(
            submission=self,
            to=self.editor_in_charge,
            accepted=True,
            date_created=timezone.now(),
            date_answered=timezone.now(),
        )
        assignment.save()

    def set_resubmission_defaults(self):
        self.open_for_reporting = True
        self.open_for_commenting = True
        if self.other_versions()[0].submitted_to_journal == 'SciPost Physics Lecture Notes':
            self.reporting_deadline = timezone.now() + datetime.timedelta(days=56)
        else:
            self.reporting_deadline = timezone.now() + datetime.timedelta(days=28)

    def copy_EIC_from_previous_version(self):
        last_version = self.other_versions()[0]
        self.editor_in_charge = last_version.editor_in_charge
        self.status = 'EICassigned'

    def copy_authors_from_previous_version(self):
        last_version = self.other_versions()[0]

        for author in last_version.authors.all():
            self.authors.add(author)
        for author in last_version.authors_claims.all():
            self.authors_claims.add(author)
        for author in last_version.authors_false_claims.all():
            self.authors_false_claims.add(author)

    def mark_other_versions_as_deprecated(self):
        for sub in self.other_versions():
            sub.is_current = False
            sub.open_for_reporting = False
            sub.status = 'resubmitted'
            sub.save()

    def other_versions(self):
        return Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=self.arxiv_identifier_wo_vn_nr
        ).exclude(pk=self.id).order_by('-arxiv_vn_nr')

    def header_as_table(self):
        # for Submission page
        header = '<table>'
        header += '<tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>'
        header += '<tr><td>Author(s): </td><td>&nbsp;</td><td>{{ author_list }}</td></tr>'
        header += '<tr><td>As Contributors: </td><td>&nbsp;</td>'
        if self.authors.all():
            header += '<td>'
            for auth in self.authors.all():
                header += ('<a href="/contributor/' + str(auth.id) + '">' + auth.user.first_name
                           + ' ' + auth.user.last_name + '</a>&nbsp;&nbsp;')
            header += '</td>'
        else:
            header += '<td>(none claimed)</td>'
        header += ('</tr>'
                   '<tr><td>arxiv Link: </td><td>&nbsp;</td>'
                   '<td><a href="{{ arxiv_link }}" target="_blank">{{ arxiv_link }}</a></td></tr>'
                   '<tr><td>Date submitted: </td><td>&nbsp;</td><td>{{ submission_date }}</td></tr>'
                   '<tr><td>Submitted by: </td><td>&nbsp;</td><td>{{ submitted_by }}</td></tr>'
                   '<tr><td>Submitted to: </td><td>&nbsp;</td><td>{{ to_journal }}</td></tr>'
                   '<tr><td>Domain(s): </td><td>&nbsp;</td><td>{{ domain }}</td></tr>'
#                   '<tr><td>Specialization: </td><td>&nbsp;</td><td>{{ spec }}</td></tr>'
                   '<tr><td>Subject area: </td><td>&nbsp;</td><td>{{ subject_area }}</td></tr>'
                   '</table>')
        template = Template(header)
        context = Context({'title': self.title, 'author_list': self.author_list,
                           'arxiv_link': self.arxiv_link, 'submission_date': self.submission_date,
                           'submitted_by': self.submitted_by,
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'domain': journals_domains_dict[self.domain],
#                           'spec': journals_spec_dict[self.specialization],
                           'subject_area': subject_areas_dict[self.subject_area],
                       })
        return template.render(context)


    def header_as_li (self):
        # for search lists
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p>'
                  '<a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">{{ title }}</a></p>'
                  '<p>by {{ author_list }}</p>'
                  '<p>Version {{ arxiv_vn_nr }}')
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version {{ arxiv_vn_nr }})'
        header += ('</p><p> Submitted {{ submission_date }} to {{ to_journal }}'
                   ' - latest activity: {{ latest_activity }}</p>'
                   #'</div></div>'
                   '</li>')
        context = Context({'arxiv_identifier_w_vn_nr': self.arxiv_identifier_w_vn_nr,
                           'arxiv_vn_nr': self.arxiv_vn_nr,
                           'title': self.title, 'author_list': self.author_list,
                           'submission_date': self.submission_date,
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M')})
        template = Template(header)
        return template.render(context)


    def header_as_li_for_authors (self):
        # includes status specification
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p><a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">{{ title }}</a></p>'
                  '<p>by {{ author_list }}</p>'
                  '<p>Version {{ arxiv_vn_nr }}')
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version {{ arxiv_vn_nr }})'
        header += ('</p><p>Submitted {{ submission_date }} to {{ to_journal }}'
                   ' - latest activity: {{ latest_activity }}</p>'
                   '<p>Status: {{ status }}</p>'
                   #'</div></div>'
                   '</li>')
        context = Context({'arxiv_identifier_w_vn_nr': self.arxiv_identifier_w_vn_nr,
                           'arxiv_vn_nr': self.arxiv_vn_nr,
                           'title': self.title, 'author_list': self.author_list,
                           'submission_date': self.submission_date,
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M'),
                           'status': submission_status_dict[self.status]})
        template = Template(header)
        return template.render(context)


    def refereeing_status_as_p (self):
        nr_ref_invited = RefereeInvitation.objects.filter(submission=self).count()
        nr_ref_accepted = RefereeInvitation.objects.filter(submission=self, accepted=True).count()
        nr_ref_declined = RefereeInvitation.objects.filter(submission=self, accepted=False).count()
        nr_invited_reports_in = Report.objects.filter(submission=self,
                                                      status=1, invited=True).count()
        nr_contrib_reports_in = Report.objects.filter(submission=self,
                                                      status=1, invited=False).count()
        nr_reports_awaiting_vetting = Report.objects.filter(submission=self, status=0).count()
        nr_reports_refused = Report.objects.filter(submission=self, status__lte=-1).count()
        header = ('<p>Nr referees invited: ' + str(nr_ref_invited) +
                  ' [' + str(nr_ref_accepted) + ' accepted/ ' +
                  str(nr_ref_declined) + ' declined/ ' +
                  str(nr_ref_invited - nr_ref_accepted - nr_ref_declined) +
                  ' response pending]</p>' +
                  '<p>Nr reports obtained: ' +
                  str(nr_invited_reports_in + nr_contrib_reports_in) + ' [' +
                  str(nr_invited_reports_in) + ' invited/ ' + str(nr_contrib_reports_in) +
                  ' contributed], nr refused: ' + str(nr_reports_refused) +
                  ', nr awaiting vetting: ' + str(nr_reports_awaiting_vetting) + '</p>')
        template = Template(header)
        context = Context({})
        return template.render(context)


    def header_as_li_for_Fellows (self):
        # for submissions pool
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p><a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">{{ title }}</a></p>'
                  '<p>by {{ author_list }}</p>'
                  '<p>Version {{ arxiv_vn_nr }}')
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version {{ arxiv_vn_nr }})'
        header += ('</p><p> Submitted {{ submission_date }} to {{ to_journal }}'
                  ' - latest activity: {{ latest_activity }}</p>')
        if self.status == 'unassigned':
            header += ('<p style="color: red">Status: {{ status }}.'
                       ' You can volunteer to become Editor-in-charge by '
                       '<a href="/submissions/volunteer_as_EIC/{{ arxiv_identifier_w_vn_nr }}">'
                       'clicking here</a>.</p>')
        else:
            header += '<p>Editor-in-charge: {{ EIC }}</p><p>Status: {{ status }}</p>'
        header += self.refereeing_status_as_p()
        header += (#'</div></div>'
                   '</li>')
        context = Context({'arxiv_identifier_w_vn_nr': self.arxiv_identifier_w_vn_nr,
                           'arxiv_vn_nr': self.arxiv_vn_nr,
                           'title': self.title, 'author_list': self.author_list,
                           'submission_date': self.submission_date,
                           'to_journal': journals_submit_dict[self.submitted_to_journal],
                           'latest_activity': self.latest_activity.strftime('%Y-%m-%d %H:%M'),
                           'EIC': str(self.editor_in_charge),
                           'status': submission_status_dict[self.status]})
        template = Template(header)
        return template.render(context)


    def simple_header_as_li (self):
        # for Lists
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p>'
                  '<a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">{{ title }}</a></p>'
                  '<p>by {{ author_list }}</p>'
                  '<p>Version {{ arxiv_vn_nr }}')
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version {{ arxiv_vn_nr }})'
        header += ('</p>'
                   #'</div></div>'
                   '</li>')
        context = Context({'arxiv_identifier_w_vn_nr': self.arxiv_identifier_w_vn_nr,
                           'arxiv_vn_nr': self.arxiv_vn_nr,
                           'title': self.title, 'author_list': self.author_list})
        template = Template(header)
        return template.render(context)


    def version_info_as_li (self):
        # for listing all versions of a Submission
        header = ('<li>'
                  #'<div class="flex-whitebox0">'
                  '<p>'
                  '<a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">version {{ arxiv_vn_nr }}</a>')
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version {{ arxiv_vn_nr }})'
        header += ('</p>'
                   #'</div>'
                   '</li>')
        context = Context({'arxiv_identifier_w_vn_nr': self.arxiv_identifier_w_vn_nr,
                           'arxiv_vn_nr': self.arxiv_vn_nr,})
        template = Template(header)
        return template.render(context)


    def status_info_as_table (self):
        header = '<table><tr><td>Current status: </td><td>&nbsp;</td><td>{{ status }}'
        context = Context({'status': submission_status_dict[self.status],})
        try:
            context['citation'] = self.publication.citation_for_web_linked()
            header += ' as {{ citation }}'
        except Publication.DoesNotExist:
            pass
        header += '</td></tr></table>'
        template = Template(header)
        return template.render(context)



######################
# Editorial workflow #
######################

ASSIGNMENT_BOOL = ((True, 'Accept'), (False, 'Decline'))
ASSIGNMENT_NULLBOOL = ((None, 'Response pending'), (True, 'Accept'), (False, 'Decline'))

ASSIGNMENT_REFUSAL_REASONS = (
    ('BUS', 'Too busy'),
    ('VAC', 'Away on vacation'),
    ('COI', 'Conflict of interest: coauthor in last 5 years'),
    ('CCC', 'Conflict of interest: close colleague'),
    ('NIR', 'Cannot give an impartial assessment'),
    ('NIE', 'Not interested enough'),
    ('DNP', 'SciPost should not even consider this paper'),
    )
assignment_refusal_reasons_dict = dict(ASSIGNMENT_REFUSAL_REASONS)

class EditorialAssignment(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    to = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    # attribute `deprecated' becomes True if another Fellow becomes Editor-in-charge
    deprecated = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS,
                                      blank=True, null=True)
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

    def header_as_li_for_eic(self):
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p><a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">{{ title }}</a></p>'
                  '<p>by {{ author_list }}</p>'
                  '<p> (submitted {{ date }} to {{ to_journal }})</p>'
                  '<p>Status: {{ status }}</p><p>Manage this Submission from its '
                  '<a href="/submissions/editorial_page/{{ arxiv_identifier_w_vn_nr }}">'
                  'Editorial Page</a>.'
                  '</p>'
                  #'</div></div>'
                  '</li>')
        template = Template(header)
        context = Context({'arxiv_identifier_w_vn_nr': self.submission.arxiv_identifier_w_vn_nr,
                           'title': self.submission.title,
                           'author_list': self.submission.author_list,
                           'date': self.submission.submission_date,
                           'to_journal': journals_submit_dict[self.submission.submitted_to_journal],
                           'status': submission_status_dict[self.submission.status]})
        return template.render(context)

    def header_as_li(self):
        """ Same as above, but without link to Editorial Page. """
        header = ('<li>'
                  #'<div class="flex-container">'
                  #'<div class="flex-whitebox0">'
                  '<p><a href="/submission/{{ arxiv_identifier_w_vn_nr }}" '
                  'class="pubtitleli">{{ title }}</a></p>'
                  '<p>by {{ author_list }}</p>'
                  '<p> (submitted {{ date }} to {{ to_journal }})</p>'
                  '<p>Status: {{ status }}</p>'
                  #'</div></div>'
                  '</li>'
              )
        template = Template(header)
        context = Context({'arxiv_identifier_w_vn_nr': self.submission.arxiv_identifier_w_vn_nr,
                           'title': self.submission.title,
                           'author_list': self.submission.author_list,
                           'date': self.submission.submission_date,
                           'to_journal': journals_submit_dict[self.submission.submitted_to_journal],
                           'status': submission_status_dict[self.submission.status]})
        return template.render(context)


class RefereeInvitation(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    referee = models.ForeignKey(Contributor, related_name='referee', blank=True, null=True,
                                on_delete=models.CASCADE)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    email_address = models.EmailField()
    # if Contributor not found, person is invited to register
    invitation_key = models.CharField(max_length=40, default='')
    date_invited = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey(Contributor, related_name='referee_invited_by',
                                   blank=True, null=True, on_delete=models.CASCADE)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    date_responded = models.DateTimeField(blank=True, null=True)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS,
                                      blank=True, null=True)
    fulfilled = models.BooleanField(default=False) # True if a Report has been submitted
    cancelled = models.BooleanField(default=False) # True if EIC has deactivated invitation

    def __str__(self):
        return (self.first_name + ' ' + self.last_name + ' to referee ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', invited on ' + self.date_invited.strftime('%Y-%m-%d'))

    # def summary_as_li(self):
    #     context = Context({'first_name': self.first_name, 'last_name': self.last_name,
    #                        'date_invited': self.date_invited.strftime('%Y-%m-%d %H:%M')})
    #     output = '<li>{{ first_name }} {{ last_name }}, invited {{ date_invited }}, '
    #     if self.accepted is not None:
    #         if self.accepted:
    #             output += '<strong style="color: green">task accepted</strong> '
    #         else:
    #             output += '<strong style="color: red">task declined</strong> '
    #         output += '{{ date_responded }}'
    #         context['date_responded'] = self.date_responded.strftime('%Y-%m-%d %H:%M')
    #     else:
    #         output += 'response pending'
    #     if self.fulfilled:
    #         output += '; Report has been delivered'
    #     template = Template(output)
    #     return template.render(context)

    def summary_as_tds(self):
        context = Context({'first_name': self.first_name, 'last_name': self.last_name,
                           'date_invited': self.date_invited.strftime('%Y-%m-%d %H:%M')})
        output = ('<td>{{ first_name }} {{ last_name }}</td><td>invited <br/>'
                  '{{ date_invited }}</td><td>')
        if self.cancelled:
            output += '<strong style="color: red;">cancelled</strong>'
        elif self.accepted is not None:
            if self.accepted:
                output += '<strong style="color: green">task accepted</strong> '
            else:
                output += '<strong style="color: red">task declined</strong> '
            output += '<br/>{{ date_responded }}'
            context['date_responded'] = self.date_responded.strftime('%Y-%m-%d %H:%M')
        else:
            output += 'response pending'
        if self.fulfilled:
            output += '<br/><strong style="color: green">task fulfilled</strong>'
        output += '</td>'
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
    (1, 'Publish as Tier I (top 10% of papers in this journal, qualifies as Select) NOTE: SELECT NOT YET OPEN, STARTS EARLY 2017'),
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
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    vetted_by = models.ForeignKey(Contributor, related_name="report_vetted_by",
                                  blank=True, null=True, on_delete=models.CASCADE)
    # `invited' filled from RefereeInvitation objects at moment of report submission
    invited = models.BooleanField(default=False)
    # `flagged' if author of report has been flagged by submission authors (surname check only)
    flagged = models.BooleanField(default=False)
    date_submitted = models.DateTimeField('date submitted')
    author = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    qualification = models.PositiveSmallIntegerField(
        choices=REFEREE_QUALIFICATION,
        verbose_name="Qualification to referee this: I am ")
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
    formatting = models.SmallIntegerField(choices=QUALITY_SPEC,
                                          verbose_name="Quality of paper formatting")
    grammar = models.SmallIntegerField(choices=QUALITY_SPEC,
                                       verbose_name="Quality of English grammar")
    #
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    remarks_for_editors = models.TextField(default='', blank=True,
                                           verbose_name='optional remarks for the Editors only')
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
        output = ('<div class="row"><div class="col-2">'
                  '<p>Strengths:</p></div><div class="col-10"><p>{{ strengths }}</p></div></div>'
                  '<div class="row"><div class="col-2">'
                  '<p>Weaknesses:</p></div><div class="col-10"><p>{{ weaknesses }}</p></div></div>'
                  '<div class="row"><div class="col-2">'
                  '<p>Report:</p></div><div class="col-10"><p>{{ report }}</p></div></div>'
                  '<div class="row"><div class="col-2">'
                  '<p>Requested changes:</p></div>'
                  '<div class="col-10"><p>{{ requested_changes }}</p></div></div>'
                  '<div class="reportRatings"><ul>'
                  '<li>validity: ' + ranking_choices_dict[self.validity] + '</li>'
                  '<li>significance: ' + ranking_choices_dict[self.significance] + '</li>'
                  '<li>originality: ' + ranking_choices_dict[self.originality] + '</li>'
                  '<li>clarity: ' + ranking_choices_dict[self.clarity] + '</li>'
                  '<li>formatting: ' + quality_spec_dict[self.formatting] + '</li>'
                  '<li>grammar: ' + quality_spec_dict[self.grammar] + '</li>'
                  '</ul></div>')
        template = Template(output)
        return template.render(context)


    def print_contents_for_editors(self):
        context = Context({'id': self.id, 'author_id': self.author.id,
                           'author_first_name': self.author.user.first_name,
                           'author_last_name': self.author.user.last_name,
                           'date_submitted': self.date_submitted.strftime("%Y-%m-%d"),
                           'remarks_for_editors': self.remarks_for_editors,
                       })
        output = '<div class="reportid">\n'
        output += '<h3><a id="report_id{{ id }}"></a>'
        if self.anonymous:
            output += '(chose public anonymity) '
        output += ('<a href="/contributor/{{ author_id }}">'
                   '{{ author_first_name }} {{ author_last_name }}</a>'
                   ' on {{ date_submitted }}</h3></div>'
                   '<div class="row"><div class="col-2">Qualification:</p></div>'
                   '<div class="col-10"><p>'
                   + ref_qualif_dict[self.qualification] + '</p></div></div>')
        output += self.print_contents()
        output += '<h3>Remarks for editors</h3><p>{{ remarks_for_editors }}</p>'
        output += '<h3>Recommendation: ' + report_rec_dict[self.recommendation] + '</h3>'
        template = Template(output)
        return template.render(context)


##########################
# EditorialCommunication #
##########################

ED_COMM_CHOICES = (
    ('EtoA', 'Editor-in-charge to Author'),
    ('EtoR', 'Editor-in-charge to Referee'),
    ('EtoS', 'Editor-in-charge to SciPost Editorial Administration'),
    ('AtoE', 'Author to Editor-in-charge'),
    ('RtoE', 'Referee to Editor-in-Charge'),
    ('StoE', 'SciPost Editorial Administration to Editor-in-charge'),
    )
ed_comm_choices_dict = dict(ED_COMM_CHOICES)

class EditorialCommunication(models.Model):
    """
    Each individual communication between Editor-in-charge
    to and from Referees and Authors becomes an instance of this class.
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    referee = models.ForeignKey(Contributor, related_name='referee_in_correspondence',
                                blank=True, null=True, on_delete=models.CASCADE)
    comtype = models.CharField(max_length=4, choices=ED_COMM_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

    def __str__ (self):
        output = self.comtype
        if self.referee is not None:
            output += ' ' + self.referee.user.first_name + ' ' + self.referee.user.last_name
        output += (' for submission ' + self.submission.title[:30] + ' by '
                   + self.submission.author_list[:30])
        return output

    def print_contents_as_li(self):
        context = Context({'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M"),
                           'text': self.text})
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
                output += (self.referee.user.first_name + ' ' +
                           self.referee.user.last_name + ' to you')
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
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    date_submitted = models.DateTimeField('date submitted', default=timezone.now)
    remarks_for_authors = models.TextField(blank=True, null=True)
    requested_changes = models.TextField(verbose_name="requested changes", blank=True, null=True)
    remarks_for_editorial_college = models.TextField(
        default='', blank=True, null=True,
        verbose_name='optional remarks for the Editorial College')
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    # Editorial Fellows who have assessed this recommendation:
    eligible_to_vote = models.ManyToManyField (Contributor, blank=True,
                                               related_name='eligible_to_vote')
    voted_for = models.ManyToManyField (Contributor, blank=True, related_name='voted_for')
    voted_against = models.ManyToManyField (Contributor, blank=True, related_name='voted_against')
    voted_abstain = models.ManyToManyField (Contributor, blank=True, related_name='voted_abstain')
    voting_deadline = models.DateTimeField('date submitted', default=timezone.now)

    def __str__(self):
        return (self.submission.title[:20] + ' by ' + self.submission.author_list[:30] +
                ', ' + report_rec_dict[self.recommendation])

    @property
    def nr_for(self):
        return self.voted_for.count()

    @property
    def nr_against(self):
        return self.voted_against.count()

    @property
    def nr_abstained(self):
        return self.voted_abstain.count()

    def print_for_authors(self):
        output = ('<h3>Date: {{ date_submitted }}</h3>'
                  '<h3>Remarks for authors</h3>'
                   '<p>{{ remarks_for_authors }}</p>'
                  '<h3>Requested changes</h3>'
                  '<p>{{ requested_changes }}</p>'
                  '<h3>Recommendation</h3>'
                  '<p>{{ recommendation }}</p>')
        context = Context({'date_submitted': self.date_submitted.strftime('%Y-%m-%d %H:%M'),
                           'remarks_for_authors': self.remarks_for_authors,
                           'requested_changes': self.requested_changes,
                           'recommendation': report_rec_dict[self.recommendation],})
        template = Template(output)
        return template.render(context)

    def print_for_Fellows(self):
        output = ('<h3>By {{ Fellow }}, formulated on {{ date_submitted }}</h3>'
                  '<h3>Remarks for authors</h3>'
                   '<p>{{ remarks_for_authors }}</p>'
                  '<h3>Requested changes</h3>'
                  '<p>{{ requested_changes }}</p>'
                  '<h3>Remarks for Editorial College</h3>'
                  '<p>{{ remarks_for_editorial_college }}</p>'
                  '<h3>Recommendation</h3>'
                  '<p>{{ recommendation }}</p>')
        context = Context({
            'Fellow': (title_dict[self.submission.editor_in_charge.title] +
                       ' ' + self.submission.editor_in_charge.user.first_name +
                       ' ' + self.submission.editor_in_charge.user.last_name),
            'date_submitted': self.date_submitted.strftime('%Y-%m-%d %H:%M'),
            'remarks_for_authors': self.remarks_for_authors,
            'requested_changes': self.requested_changes,
            'remarks_for_editorial_college': self.remarks_for_editorial_college,
            'recommendation': report_rec_dict[self.recommendation],})
        template = Template(output)
        return template.render(context)
