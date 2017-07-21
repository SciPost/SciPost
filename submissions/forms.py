from django import forms
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone

from guardian.shortcuts import assign_perm

from .constants import ASSIGNMENT_BOOL, ASSIGNMENT_REFUSAL_REASONS, STATUS_RESUBMITTED,\
                       REPORT_ACTION_CHOICES, REPORT_REFUSAL_CHOICES, STATUS_REVISION_REQUESTED,\
                       STATUS_REJECTED, STATUS_REJECTED_VISIBLE, STATUS_RESUBMISSION_INCOMING,\
                       STATUS_DRAFT, STATUS_UNVETTED, REPORT_ACTION_ACCEPT, REPORT_ACTION_REFUSE,\
                       STATUS_VETTED
from .exceptions import InvalidReportVettingValue
from .models import Submission, RefereeInvitation, Report, EICRecommendation, EditorialAssignment

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.services import ArxivCaller
from scipost.models import Contributor

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, Submit

import strings


class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    abstract = forms.CharField(max_length=1000, required=False)
    subject_area = forms.CharField(max_length=10, required=False, widget=forms.Select(
                                   choices=((None, 'Show all'),) + SCIPOST_SUBJECT_AREAS[0][1]))

    def search_results(self):
        """Return all Submission objects according to search"""
        return Submission.objects.public_overcomplete().filter(
            title__icontains=self.cleaned_data.get('title', ''),
            author_list__icontains=self.cleaned_data.get('author', ''),
            abstract__icontains=self.cleaned_data.get('abstract', ''),
            subject_area__icontains=self.cleaned_data.get('subject_area', '')
        )


###############################
# Submission and resubmission #
###############################

class SubmissionChecks:
    """
    Use this class as a blueprint containing checks which should be run
    in multiple forms.
    """
    is_resubmission = False
    last_submission = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prefill `is_resubmission` property if data is coming from initial data
        if kwargs.get('initial', None):
            if kwargs['initial'].get('is_resubmission', None):
                self.is_resubmission = kwargs['initial']['is_resubmission'] in ('True', True)

        # `is_resubmission` property if data is coming from (POST) request
        if kwargs.get('data', None):
            if kwargs['data'].get('is_resubmission', None):
                self.is_resubmission = kwargs['data']['is_resubmission'] in ('True', True)

    def _submission_already_exists(self, identifier):
        if Submission.objects.filter(arxiv_identifier_w_vn_nr=identifier).exists():
            error_message = 'This preprint version has already been submitted to SciPost.'
            raise forms.ValidationError(error_message, code='duplicate')

    def _call_arxiv(self, identifier):
        caller = ArxivCaller(identifier)
        if caller.is_valid:
            self.arxiv_data = ArxivCaller(identifier).data
            self.metadata = ArxivCaller(identifier).metadata
        else:
            error_message = 'A preprint associated to this identifier does not exist.'
            raise forms.ValidationError(error_message)

    def _submission_is_already_published(self, identifier):
        published_id = None
        if 'arxiv_doi' in self.arxiv_data:
            published_id = self.arxiv_data['arxiv_doi']
        elif 'arxiv_journal_ref' in self.arxiv_data:
            published_id = self.arxiv_data['arxiv_journal_ref']

        if published_id:
            error_message = ('This paper has been published under DOI %(published_id)s'
                             '. Please comment on the published version.'),
            raise forms.ValidationError(error_message, code='published',
                                        params={'published_id': published_id})

    def _submission_previous_version_is_valid_for_submission(self, identifier):
        '''Check if previous submitted versions have the appropriate status.'''
        identifiers = self.identifier_into_parts(identifier)
        submission = (Submission.objects
                      .filter(arxiv_identifier_wo_vn_nr=identifiers['arxiv_identifier_wo_vn_nr'])
                      .order_by('arxiv_vn_nr').last())

        # If submissions are found; check their statuses
        if submission:
            self.last_submission = submission
            if submission.status == STATUS_REVISION_REQUESTED:
                self.is_resubmission = True
            elif submission.status in [STATUS_REJECTED, STATUS_REJECTED_VISIBLE]:
                error_message = ('This arXiv preprint has previously undergone refereeing '
                                 'and has been rejected. Resubmission is only possible '
                                 'if the manuscript has been substantially reworked into '
                                 'a new arXiv submission with distinct identifier.')
                raise forms.ValidationError(error_message)
            else:
                error_message = ('There exists a preprint with this arXiv identifier '
                                 'but an earlier version number, which is still undergoing '
                                 'peer refereeing. '
                                 'A resubmission can only be performed after request '
                                 'from the Editor-in-charge. Please wait until the '
                                 'closing of the previous refereeing round and '
                                 'formulation of the Editorial Recommendation '
                                 'before proceeding with a resubmission.')
                raise forms.ValidationError(error_message)

    def submission_is_resubmission(self):
        return self.is_resubmission

    def identifier_into_parts(self, identifier):
        data = {
            'arxiv_identifier_w_vn_nr': identifier,
            'arxiv_identifier_wo_vn_nr': identifier.rpartition('v')[0],
            'arxiv_vn_nr': int(identifier.rpartition('v')[2])
        }
        return data

    def do_pre_checks(self, identifier):
        self._submission_already_exists(identifier)
        self._call_arxiv(identifier)
        self._submission_is_already_published(identifier)
        self._submission_previous_version_is_valid_for_submission(identifier)


class SubmissionIdentifierForm(SubmissionChecks, forms.Form):
    IDENTIFIER_PATTERN_NEW = r'^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$'
    IDENTIFIER_PLACEHOLDER = 'new style (with version nr) ####.####(#)v#(#)'

    identifier = forms.RegexField(regex=IDENTIFIER_PATTERN_NEW, strip=True,
                                  #   help_text=strings.arxiv_query_help_text,
                                  error_messages={'invalid': strings.arxiv_query_invalid},
                                  widget=forms.TextInput({'placeholder': IDENTIFIER_PLACEHOLDER}))

    def clean_identifier(self):
        identifier = self.cleaned_data['identifier']
        self.do_pre_checks(identifier)
        return identifier

    def _gather_data_from_last_submission(self):
        '''Return dictionary with data coming from previous submission version.'''
        if self.submission_is_resubmission():
            data = {
                'is_resubmission': True,
                'discipline': self.last_submission.discipline,
                'domain': self.last_submission.domain,
                'referees_flagged': self.last_submission.referees_flagged,
                'referees_suggested': self.last_submission.referees_suggested,
                'secondary_areas': self.last_submission.secondary_areas,
                'subject_area': self.last_submission.subject_area,
                'submitted_to_journal': self.last_submission.submitted_to_journal,
                'submission_type': self.last_submission.submission_type,
            }
        return data or {}

    def request_arxiv_preprint_form_prefill_data(self):
        '''Return dictionary to prefill `RequestSubmissionForm`.'''
        form_data = self.arxiv_data
        form_data.update(self.identifier_into_parts(self.cleaned_data['identifier']))
        if self.submission_is_resubmission():
            form_data.update(self._gather_data_from_last_submission())
        return form_data


class RequestSubmissionForm(SubmissionChecks, forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            'is_resubmission',
            'discipline',
            'submitted_to_journal',
            'submission_type',
            'domain',
            'subject_area',
            'secondary_areas',
            'title',
            'author_list',
            'abstract',
            'arxiv_identifier_w_vn_nr',
            'arxiv_link',
            'author_comments',
            'list_of_changes',
            'remarks_for_editors',
            'referees_suggested',
            'referees_flagged'
        ]
        widgets = {
            'is_resubmission': forms.HiddenInput(),
            'arxiv_identifier_w_vn_nr': forms.HiddenInput(),
            'secondary_areas': forms.SelectMultiple(choices=SCIPOST_SUBJECT_AREAS)
        }

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by', None)
        super().__init__(*args, **kwargs)

        if not self.submission_is_resubmission():
            # These fields are only available for resubmissions
            del self.fields['author_comments']
            del self.fields['list_of_changes']
        else:
            self.fields['author_comments'].widget.attrs.update({
                'placeholder': 'Your resubmission letter (will be viewable online)', })
            self.fields['list_of_changes'].widget.attrs.update({
                'placeholder': 'Give a point-by-point list of changes (will be viewable online)'})

        # Update placeholder for the other fields
        self.fields['arxiv_link'].widget.attrs.update({
            'placeholder': 'ex.:  arxiv.org/abs/1234.56789v1'})
        self.fields['abstract'].widget.attrs.update({'cols': 100})
        self.fields['remarks_for_editors'].widget.attrs.update({
            'placeholder': 'Any private remarks (for the editors only)', })
        self.fields['referees_suggested'].widget.attrs.update({
            'placeholder': 'Optional: names of suggested referees',
            'rows': 3})
        self.fields['referees_flagged'].widget.attrs.update({
            'placeholder': ('Optional: names of referees whose reports should'
                            ' be treated with caution (+ short reason)'),
            'rows': 3})

    def clean(self, *args, **kwargs):
        """
        Do all prechecks which are also done in the prefiller.
        """
        cleaned_data = super().clean(*args, **kwargs)
        self.do_pre_checks(cleaned_data['arxiv_identifier_w_vn_nr'])
        return cleaned_data

    def clean_author_list(self):
        """
        Important check!

        The submitting user must be an author of the submission.
        Also possibly may be extended to check permissions and give ultimate submission
        power to certain user groups.
        """
        author_list = self.cleaned_data['author_list']
        if not self.requested_by.last_name.lower() in author_list.lower():
            error_message = ('Your name does not match that of any of the authors. '
                             'You are not authorized to submit this preprint.')
            raise forms.ValidationError(error_message, code='not_an_author')
        return author_list

    @transaction.atomic
    def copy_and_save_data_from_resubmission(self, submission):
        """
        Fill given Submission with data coming from last_submission in the SubmissionChecks
        blueprint.
        """
        if not self.last_submission:
            raise Submission.DoesNotExist

        # Open for comment and reporting
        submission.open_for_reporting = True
        submission.open_for_commenting = True

        # Close last submission
        self.last_submission.is_current = False
        self.last_submission.open_for_reporting = False
        self.last_submission.status = STATUS_RESUBMITTED
        self.last_submission.save()

        # Editor-in-charge
        submission.editor_in_charge = self.last_submission.editor_in_charge
        submission.status = STATUS_RESUBMISSION_INCOMING

        # Author claim fields
        submission.authors.add(*self.last_submission.authors.all())
        submission.authors_claims.add(*self.last_submission.authors_claims.all())
        submission.authors_false_claims.add(*self.last_submission.authors_false_claims.all())
        submission.save()
        return submission

    @transaction.atomic
    def reassign_eic_and_admins(self, submission):
        # Assign permissions
        assign_perm('can_take_editorial_actions', submission.editor_in_charge.user, submission)
        ed_admins = Group.objects.get(name='Editorial Administrators')
        assign_perm('can_take_editorial_actions', ed_admins, submission)

        # Assign editor
        assignment = EditorialAssignment(
            submission=submission,
            to=submission.editor_in_charge,
            accepted=True
        )
        assignment.save()
        submission.save()
        return submission

    @transaction.atomic
    def save(self):
        """
        Prefill instance before save.

        Because of the ManyToManyField on `authors`, commit=False for this form
        is disabled. Saving the form without the database call may loose `authors`
        data without notice.
        """
        submission = super().save(commit=False)
        submission.submitted_by = self.requested_by.contributor

        # Save metadata directly from ArXiv call without possible user interception
        submission.metadata = self.metadata

        # Update identifiers
        identifiers = self.identifier_into_parts(submission.arxiv_identifier_w_vn_nr)
        submission.arxiv_identifier_wo_vn_nr = identifiers['arxiv_identifier_wo_vn_nr']
        submission.arxiv_vn_nr = identifiers['arxiv_vn_nr']

        # Save
        submission.save()
        if self.submission_is_resubmission():
            submission = self.copy_and_save_data_from_resubmission(submission)
            submission = self.reassign_eic_and_admins(submission)
        submission.authors.add(self.requested_by.contributor)
        return submission


######################
# Editorial workflow #
######################

class AssignSubmissionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        discipline = kwargs.pop('discipline')
        super(AssignSubmissionForm, self).__init__(*args, **kwargs)
        self.fields['editor_in_charge'] = forms.ModelChoiceField(
            queryset=Contributor.objects.filter(user__groups__name='Editorial College',
                                                user__contributor__discipline=discipline,
                                                ).order_by('user__last_name'),
            required=True, label='Select an Editor-in-charge')


class ConsiderAssignmentForm(forms.Form):
    accept = forms.ChoiceField(widget=forms.RadioSelect, choices=ASSIGNMENT_BOOL,
                               label="Are you willing to take charge of this Submission?")
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS, required=False)


class RefereeSelectForm(forms.Form):
    last_name = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(RefereeSelectForm, self).__init__(*args, **kwargs)
        self.fields['last_name'].widget.attrs.update(
            {'size': 20, 'placeholder': 'Search in contributors database'})


class RefereeRecruitmentForm(forms.ModelForm):
    class Meta:
        model = RefereeInvitation
        fields = ['title', 'first_name', 'last_name', 'email_address']

    def __init__(self, *args, **kwargs):
        super(RefereeRecruitmentForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'size': 20})
        self.fields['last_name'].widget.attrs.update({'size': 20})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(Field('title'), Field('first_name'), Field('last_name'),
                Field('email_address'),
                Submit('submit', 'Send invitation', css_class="submitButton"),
                css_class="flex-whitebox320")
        )


class ConsiderRefereeInvitationForm(forms.Form):
    accept = forms.ChoiceField(widget=forms.RadioSelect, choices=ASSIGNMENT_BOOL,
                               label="Are you willing to referee this Submission?")
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS, required=False)


class SetRefereeingDeadlineForm(forms.Form):
    deadline = forms.DateField(required=False, label='', widget=forms.SelectDateWidget)


class VotingEligibilityForm(forms.Form):

    def __init__(self, *args, **kwargs):
        discipline = kwargs.pop('discipline')
        subject_area = kwargs.pop('subject_area')
        super(VotingEligibilityForm, self).__init__(*args, **kwargs)
        self.fields['eligible_Fellows'] = forms.ModelMultipleChoiceField(
            queryset=Contributor.objects.filter(
                user__groups__name__in=['Editorial College'],
                user__contributor__discipline=discipline,
                user__contributor__expertises__contains=[subject_area]
            ).order_by('user__last_name'),
            widget=forms.CheckboxSelectMultiple({'checked': 'checked'}),
            required=True, label='Eligible for voting',
        )


############
# Reports:
############

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['qualification', 'strengths', 'weaknesses', 'report', 'requested_changes',
                  'validity', 'significance', 'originality', 'clarity', 'formatting', 'grammar',
                  'recommendation', 'remarks_for_editors', 'anonymous']

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            if kwargs['instance'].is_followup_report:
                # Prefill data from latest report in the series
                latest_report = kwargs['instance'].latest_report_from_series()
                kwargs.update({
                    'initial': {
                        'qualification': latest_report.qualification,
                        'anonymous': latest_report.anonymous
                    }
                })

        super(ReportForm, self).__init__(*args, **kwargs)
        self.fields['strengths'].widget.attrs.update({
            'placeholder': ('Give a point-by-point '
                            '(numbered 1-, 2-, ...) list of the paper\'s strengths'),
            'rows': 10,
            'cols': 100
        })
        self.fields['weaknesses'].widget.attrs.update({
            'placeholder': ('Give a point-by-point '
                            '(numbered 1-, 2-, ...) list of the paper\'s weaknesses'),
            'rows': 10,
            'cols': 100
        })
        self.fields['report'].widget.attrs.update({'placeholder': 'Your general remarks',
                                                   'rows': 10, 'cols': 100})
        self.fields['requested_changes'].widget.attrs.update({
            'placeholder': 'Give a numbered (1-, 2-, ...) list of specifically requested changes',
            'cols': 100
        })

        # If the Report is not a followup: Explicitly assign more fields as being required!
        if not self.instance.is_followup_report:
            required_fields = [
                'strengths',
                'weaknesses',
                'requested_changes',
                'validity',
                'significance',
                'originality',
                'clarity',
                'formatting',
                'grammar'
            ]
            for field in required_fields:
                self.fields[field].required = True

        # Let user know the field is required!
        for field in self.fields:
            if self.fields[field].required:
                self.fields[field].label += ' *'

    def save(self, submission):
        """
        Update meta data if ModelForm is submitted (non-draft).
        Possibly overwrite the default status if user asks for saving as draft.
        """
        report = super().save(commit=False)

        report.submission = submission
        report.date_submitted = timezone.now()

        # Save with right status asked by user
        if 'save_draft' in self.data:
            report.status = STATUS_DRAFT
        elif 'save_submit' in self.data:
            report.status = STATUS_UNVETTED

            # Update invitation and report meta data if exist
            invitation = submission.referee_invitations.filter(referee=report.author).first()
            if invitation:
                invitation.fulfilled = True
                invitation.save()
                report.invited = True

            # Check if report author if the report is being flagged on the submission
            if submission.referees_flagged:
                if report.author.user.last_name in submission.referees_flagged:
                    report.flagged = True
        report.save()
        return report


class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect,
                                      choices=REPORT_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(),
                                           label='Justification (optional)', required=False)
    report = forms.ModelChoiceField(queryset=Report.objects.awaiting_vetting(), required=True,
                                    widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(VetReportForm, self).__init__(*args, **kwargs)
        self.fields['email_response_field'].widget.attrs.update({
            'placeholder': ('Optional: give a textual justification '
                            '(will be included in the email to the Report\'s author)'),
            'rows': 5
        })

    def clean_refusal_reason(self):
        '''Require a refusal reason if report is rejected.'''
        reason = self.cleaned_data['refusal_reason']
        if self.cleaned_data['action_option'] == REPORT_ACTION_REFUSE:
            if not reason:
                self.add_error('refusal_reason', 'A reason must be given to refuse a report.')
        return reason

    def process_vetting(self, current_contributor):
        '''Set the right report status and update submission fields if needed.'''
        report = self.cleaned_data['report']
        report.vetted_by = current_contributor
        if self.cleaned_data['action_option'] == REPORT_ACTION_ACCEPT:
            # Accept the report as is
            report.status = STATUS_VETTED
            report.submission.latest_activity = timezone.now()
            report.submission.save()
        elif self.cleaned_data['action_option'] == REPORT_ACTION_REFUSE:
            # The report is rejected
            report.status = self.cleaned_data['refusal_reason']
        else:
            raise InvalidReportVettingValue(self.cleaned_data['action_option'])
        report.save()
        return report


###################
# Communications #
###################

class EditorialCommunicationForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(), label='')

    def __init__(self, *args, **kwargs):
        super(EditorialCommunicationForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update(
            {'rows': 5, 'cols': 50, 'placeholder': 'Write your message in this box.'})


######################
# EIC Recommendation #
######################

class EICRecommendationForm(forms.ModelForm):
    class Meta:
        model = EICRecommendation
        fields = ['recommendation',
                  'remarks_for_authors', 'requested_changes',
                  'remarks_for_editorial_college']

    def __init__(self, *args, **kwargs):
        super(EICRecommendationForm, self).__init__(*args, **kwargs)
        self.fields['remarks_for_authors'].widget.attrs.update(
            {'placeholder': 'Your general remarks for the authors',
             'rows': 10, 'cols': 100})
        self.fields['requested_changes'].widget.attrs.update(
            {'placeholder': 'If you request revisions, give a numbered (1-, 2-, ...) list of specifically requested changes',
             'cols': 100})
        self.fields['remarks_for_editorial_college'].widget.attrs.update(
            {'placeholder': 'If you recommend to accept or refuse, the Editorial College will vote; write any relevant remarks for the EC here.'})


###############
# Vote form #
###############

class RecommendationVoteForm(forms.Form):
    vote = forms.ChoiceField(widget=forms.RadioSelect,
                             choices=[('agree', 'Agree'),
                                      ('disagree', 'Disagree'),
                                      ('abstain', 'Abstain')],
                             label='',
                             )
    remark = forms.CharField(widget=forms.Textarea(), label='', required=False)

    def __init__(self, *args, **kwargs):
        super(RecommendationVoteForm, self).__init__(*args, **kwargs)
        self.fields['remark'].widget.attrs.update(
            {'rows': 3, 'cols': 30, 'placeholder': 'Your remarks (optional)'})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML('<h3>Your position on this recommendation:</h3>'),
                    Field('vote'),
                    css_class='flex-Fellowactionbox'),
                Div(Field('remark'), css_class='flex-Fellowactionbox'),
                Div(Submit('submit', 'Cast your vote', css_class='submitButton'),
                    css_class='flex-Fellowactionbox'),
                css_class='flex-container')
        )


class SubmissionCycleChoiceForm(forms.ModelForm):
    referees_reinvite = forms.ModelMultipleChoiceField(queryset=RefereeInvitation.objects.none(),
                                                       widget=forms.CheckboxSelectMultiple({
                                                            'checked': 'checked'}),
                                                       required=False, label='Reinvite referees')

    class Meta:
        model = Submission
        fields = ('refereeing_cycle',)
        widgets = {'refereeing_cycle': forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['refereeing_cycle'].default = None
        other_submission = self.instance.other_versions().first()
        if other_submission:
            self.fields['referees_reinvite'].queryset = other_submission.referee_invitations.all()
