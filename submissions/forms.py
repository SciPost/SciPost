import datetime
import re

from django import forms
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .constants import ASSIGNMENT_BOOL, ASSIGNMENT_REFUSAL_REASONS, STATUS_RESUBMITTED,\
                       REPORT_ACTION_CHOICES, REPORT_REFUSAL_CHOICES, STATUS_REVISION_REQUESTED,\
                       STATUS_REJECTED, STATUS_REJECTED_VISIBLE, STATUS_RESUBMISSION_INCOMING,\
                       STATUS_DRAFT, STATUS_UNVETTED, REPORT_ACTION_ACCEPT, REPORT_ACTION_REFUSE,\
                       STATUS_VETTED, EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS, SUBMISSION_STATUS,\
                       POST_PUBLICATION_STATUSES, REPORT_POST_EDREC, REPORT_NORMAL
from . import exceptions, helpers
from .models import Submission, RefereeInvitation, Report, EICRecommendation, EditorialAssignment,\
                    iThenticateReport, EditorialCommunication

from colleges.models import Fellowship
from journals.constants import SCIPOST_JOURNAL_PHYSICS_PROC
from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.services import ArxivCaller
from scipost.models import Contributor
import strings

import iThenticate


class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    abstract = forms.CharField(max_length=1000, required=False)
    subject_area = forms.CharField(max_length=10, required=False, widget=forms.Select(
                                   choices=((None, 'Show all'),) + SCIPOST_SUBJECT_AREAS[0][1]))

    def search_results(self):
        """Return all Submission objects according to search"""
        return Submission.objects.public_newest().filter(
            title__icontains=self.cleaned_data.get('title', ''),
            author_list__icontains=self.cleaned_data.get('author', ''),
            abstract__icontains=self.cleaned_data.get('abstract', ''),
            subject_area__icontains=self.cleaned_data.get('subject_area', '')
        )


class SubmissionPoolFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=((None, 'All submissions currently under evaluation'),) + SUBMISSION_STATUS,
        required=False)
    editor_in_charge = forms.BooleanField(
        label='Show only Submissions for which I am editor in charge.', required=False)

    def search(self, queryset, current_user):
        if self.cleaned_data.get('status'):
            # Do extra check on non-required field to never show errors on template
            queryset = queryset.pool_full(current_user).filter(status=self.cleaned_data['status'])
        else:
            # If no specific status if requested, just return the Pool by default
            queryset = queryset.pool(current_user)

        if self.cleaned_data.get('editor_in_charge') and hasattr(current_user, 'contributor'):
            queryset = queryset.filter(editor_in_charge=current_user.contributor)

        return queryset.order_by('-submission_date')

    def status_verbose(self):
        try:
            return dict(SUBMISSION_STATUS)[self.cleaned_data['status']]
        except KeyError:
            return ''


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
        self.requested_by = kwargs.pop('requested_by', None)
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
                if self.requested_by.contributor not in submission.authors.all():
                    error_message = ('There exists a preprint with this arXiv identifier '
                                     'but an earlier version number. Resubmission is only possible'
                                     ' if you are a registered author of this manuscript.')
                    raise forms.ValidationError(error_message)
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

    def arxiv_meets_regex(self, identifier, journal_code):
        if journal_code in EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS.keys():
            regex = EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS[journal_code]
        else:
            regex = EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS['default']

        pattern = re.compile(regex)
        if not pattern.match(identifier):
            # No match object returned, identifier is invalid
            error_message = ('The journal you want to submit to does not allow for this'
                             ' arXiv identifier. Please contact SciPost if you have'
                             ' any further questions.')
            raise forms.ValidationError(error_message, code='submitted_to_journal')

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
    IDENTIFIER_PATTERN_NEW = r'^[0-9]{4,}\.[0-9]{4,5}v[0-9]{1,2}$'
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
            'proceedings',
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

        # Proceedings submission
        qs = self.fields['proceedings'].queryset.open_for_submission()
        self.fields['proceedings'].queryset = qs
        self.fields['proceedings'].empty_label = None
        if not qs.exists():
            # Open the proceedings Journal for submission
            def filter_proceedings(item):
                return item[0] != SCIPOST_JOURNAL_PHYSICS_PROC

            self.fields['submitted_to_journal'].choices = filter(
                filter_proceedings, self.fields['submitted_to_journal'].choices)
            del self.fields['proceedings']

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
        self.arxiv_meets_regex(cleaned_data['arxiv_identifier_w_vn_nr'],
                               cleaned_data['submitted_to_journal'])

        if self.cleaned_data['submitted_to_journal'] != SCIPOST_JOURNAL_PHYSICS_PROC:
            try:
                del self.cleaned_data['proceedings']
            except KeyError:
                # No proceedings returned to data
                return cleaned_data

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
        # Assign editor
        assignment = EditorialAssignment(
            submission=submission,
            to=submission.editor_in_charge,
            accepted=True
        )
        assignment.save()
        submission.save()
        return submission

    def set_pool(self, submission):
        qs = Fellowship.objects.active()
        fellows = qs.regular().filter(
            contributor__discipline=submission.discipline).return_active_for_submission(submission)
        submission.fellows.set(fellows)

        if submission.proceedings:
            # Add Guest Fellowships if the Submission is a Proceedings manuscript
            guest_fellows = qs.guests().filter(
                proceedings=submission.proceedings).return_active_for_submission(submission)
            submission.fellows.add(*guest_fellows)

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
        self.set_pool(submission)
        return submission


class SubmissionReportsForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['pdf_refereeing_pack']


######################
# Editorial workflow #
######################

class EditorialAssignmentForm(forms.ModelForm):
    class Meta:
        model = EditorialAssignment
        fields = ('to',)
        labels = {
            'to': 'Fellow',
        }

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop('submission')
        super().__init__(*args, **kwargs)
        self.fields['to'].queryset = Contributor.objects.available().filter(
            fellowships__pool=self.submission).distinct().order_by('user__last_name')

    def save(self, commit=True):
        self.instance.submission = self.submission
        return super().save(commit)


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


class ConsiderRefereeInvitationForm(forms.Form):
    accept = forms.ChoiceField(widget=forms.RadioSelect, choices=ASSIGNMENT_BOOL,
                               label="Are you willing to referee this Submission?")
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS, required=False)


class SetRefereeingDeadlineForm(forms.Form):
    deadline = forms.DateField(required=False, label='', widget=forms.SelectDateWidget)

    def clean_deadline(self):
        if not self.cleaned_data.get('deadline'):
            self.add_error('deadline', 'Please use a valid date.')
        return self.cleaned_data.get('deadline')


class VotingEligibilityForm(forms.ModelForm):
    eligible_fellows = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.none(),
        widget=forms.CheckboxSelectMultiple({'checked': 'checked'}),
        required=True, label='Eligible for voting')

    class Meta:
        model = EICRecommendation
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eligible_fellows'].queryset = Contributor.objects.filter(
                fellowships__pool=self.instance.submission,
                expertises__contains=[self.instance.submission.subject_area]
                ).order_by('user__last_name')

    def save(self, commit=True):
        recommendation = self.instance
        recommendation.eligible_to_vote = self.cleaned_data['eligible_fellows']
        submission = self.instance.submission
        submission.status = 'put_to_EC_voting'

        if commit:
            recommendation.save()
            submission.save()
            recommendation.voted_for.add(recommendation.submission.editor_in_charge)
        return recommendation


############
# Reports:
############

class ReportPDFForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['pdf_report']


class ReportForm(forms.ModelForm):
    report_type = REPORT_NORMAL

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

        self.submission = kwargs.pop('submission')

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

        if self.submission.status in POST_PUBLICATION_STATUSES:
            self.report_type = REPORT_POST_EDREC

    def save(self):
        """
        Update meta data if ModelForm is submitted (non-draft).
        Possibly overwrite the default status if user asks for saving as draft.
        """
        report = super().save(commit=False)
        report.report_type = self.report_type

        report.submission = self.submission
        report.date_submitted = timezone.now()

        # Save with right status asked by user
        if 'save_draft' in self.data:
            report.status = STATUS_DRAFT
        elif 'save_submit' in self.data:
            report.status = STATUS_UNVETTED

            # Update invitation and report meta data if exist
            updated_invitations = self.submission.referee_invitations.filter(
                referee=report.author).update(fulfilled=True)
            if updated_invitations > 0:
                report.invited = True

            # Check if report author if the report is being flagged on the submission
            if self.submission.referees_flagged:
                if report.author.user.last_name in self.submission.referees_flagged:
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
            raise exceptions.InvalidReportVettingValue(self.cleaned_data['action_option'])
        report.save()
        return report


###################
# Communications #
###################

class EditorialCommunicationForm(forms.ModelForm):
    class Meta:
        model = EditorialCommunication
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Write your message in this box.'
            }),
        }


######################
# EIC Recommendation #
######################

class EICRecommendationForm(forms.ModelForm):
    DAYS_TO_VOTE = 7
    assignment = None
    earlier_recommendations = None

    class Meta:
        model = EICRecommendation
        fields = [
            'recommendation',
            'remarks_for_authors',
            'requested_changes',
            'remarks_for_editorial_college'
        ]
        widgets = {
            'remarks_for_authors': forms.Textarea({
                'placeholder': 'Your general remarks for the authors',
                'rows': 10,
            }),
            'requested_changes': forms.Textarea({
                'placeholder': ('If you request revisions, give a numbered (1-, 2-, ...)'
                                ' list of specifically requested changes'),
            }),
            'remarks_for_editorial_college': forms.Textarea({
                'placeholder': ('If you recommend to accept or refuse, the Editorial College '
                                'will vote; write any relevant remarks for the EC here.'),
            }),
        }

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop('submission')
        self.reformulate = kwargs.pop('reformulate', False)
        if self.reformulate:
            self.load_earlier_recommendations()
            latest_recommendation = self.earlier_recommendations.first()
            if latest_recommendation:
                kwargs['initial'] = {
                    'recommendation': latest_recommendation.recommendation,
                    'remarks_for_authors': latest_recommendation.remarks_for_authors,
                    'requested_changes': latest_recommendation.requested_changes,
                    'remarks_for_editorial_college':
                        latest_recommendation.remarks_for_editorial_college,
                }

        super().__init__(*args, **kwargs)
        self.load_assignment()

    def save(self, commit=True):
        recommendation = super().save(commit=False)
        recommendation.submission = self.submission
        recommendation.voting_deadline += datetime.timedelta(days=self.DAYS_TO_VOTE)  # Test this
        if self.reformulate:
            # Increment version number
            recommendation.version = len(self.earlier_recommendations) + 1
            event_text = 'The Editorial Recommendation has been reformulated: {}.'
        else:
            event_text = 'An Editorial Recommendation has been formulated: {}.'

        if recommendation.recommendation in [1, 2, 3, -3]:
            # Accept/Reject: Forward to the Editorial College for voting
            self.submission.status = 'voting_in_preparation'

            if commit:
                # Add SubmissionEvent for EIC only
                self.submission.add_event_for_eic(event_text.format(
                        recommendation.get_recommendation_display()))
        elif recommendation.recommendation in [-1, -2]:
            # Minor/Major revision: return to Author; ask to resubmit
            self.submission.status = 'revision_requested'
            self.submission.open_for_reporting = False

            if commit:
                # Add SubmissionEvents for both Author and EIC
                self.submission.add_general_event(event_text.format(
                        recommendation.get_recommendation_display()))

        if commit:
            if self.earlier_recommendations:
                self.earlier_recommendations.update(active=False)

                # All reports already submitted are now formulated *after* eic rec formulation
                Report.objects.filter(
                    submission__eicrecommendations__in=self.earlier_recommendations).update(
                        report_type=REPORT_NORMAL)

            recommendation.save()
            self.submission.save()

            if self.assignment:
                # The EIC has fulfilled this editorial assignment.
                self.assignment.completed = True
                self.assignment.save()
        return recommendation

    def revision_requested(self):
        return self.instance.recommendation in [-1, -2]

    def has_assignment(self):
        return self.assignment is not None

    def load_assignment(self):
        # Find EditorialAssignment for Submission
        try:
            self.assignment = self.submission.editorial_assignments.accepted().get(
                to=self.submission.editor_in_charge)
            return True
        except EditorialAssignment.DoesNotExist:
            return False

    def load_earlier_recommendations(self):
        self.earlier_recommendations = self.submission.eicrecommendations.all()


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
        other_submissions = self.instance.other_versions_pool.all()
        if other_submissions:
            self.fields['referees_reinvite'].queryset = RefereeInvitation.objects.filter(
                submission__in=other_submissions).distinct()


class iThenticateReportForm(forms.ModelForm):
    class Meta:
        model = iThenticateReport
        fields = []

    def __init__(self, submission, *args, **kwargs):
        self.submission = submission
        super().__init__(*args, **kwargs)

        if kwargs.get('files', {}).get('file'):
            # Add file field if file data is coming in!
            self.fields['file'] = forms.FileField()

    def clean(self):
        cleaned_data = super().clean()
        doc_id = self.instance.doc_id
        if not doc_id and not self.fields.get('file'):
            try:
                cleaned_data['document'] = helpers.retrieve_pdf_from_arxiv(
                                        self.submission.arxiv_identifier_w_vn_nr)
            except exceptions.ArxivPDFNotFound:
                self.add_error(None, ('The pdf could not be found at arXiv.'
                                      ' Please upload the pdf manually.'))
                self.fields['file'] = forms.FileField()
        elif not doc_id and cleaned_data.get('file'):
            cleaned_data['document'] = cleaned_data['file'].read()
        elif doc_id:
            self.document_id = doc_id

        # Login client to append login-check to form
        self.client = self.get_client()

        if not self.client:
            return None

        # Document (id) is found
        if cleaned_data.get('document'):
            self.document = cleaned_data['document']
            self.response = self.call_ithenticate()
        elif hasattr(self, 'document_id'):
            self.response = self.call_ithenticate()

        if hasattr(self, 'response') and self.response:
            return cleaned_data

        # Don't return anything as someone submitted invalid data for the form at this point!
        return None

    def save(self, *args, **kwargs):
        data = self.response

        report, created = iThenticateReport.objects.get_or_create(doc_id=data['id'])

        if not created:
            try:
                iThenticateReport.objects.filter(doc_id=data['id']).update(
                    uploaded_time=data['uploaded_time'],
                    processed_time=data['processed_time'],
                    percent_match=data['percent_match'],
                    part_id=data.get('parts', [{}])[0].get('id')
                )
            except KeyError:
                pass
        else:
            report.save()
            self.submission.plagiarism_report = report
            self.submission.save()
        return report

    def call_ithenticate(self):
        if hasattr(self, 'document_id'):
            # Update iThenticate status
            return self.update_status()
        elif hasattr(self, 'document'):
            # Upload iThenticate document first time
            return self.upload_document()

    def get_client(self):
        client = iThenticate.API.Client(settings.ITHENTICATE_USERNAME,
                                        settings.ITHENTICATE_PASSWORD)
        if client.login():
            return client
        self.add_error(None, "Failed to login to iThenticate.")
        return None

    def update_status(self):
        client = self.client
        response = client.documents.get(self.document_id)
        if response['status'] == 200:
            return response.get('data')[0].get('documents')[0]
        self.add_error(None, "Updating failed. iThenticate didn't return valid data [1]")

        for msg in client.messages:
            self.add_error(None, msg)
        return None

    def upload_document(self):
        from .plagiarism import iThenticate
        plagiarism = iThenticate()
        data = plagiarism.upload_submission(self.document, self.submission)

        # Give feedback to the user
        if not data:
            self.add_error(None, "Updating failed. iThenticate didn't return valid data [3]")
            for msg in plagiarism.get_messages():
                self.add_error(None, msg)
            return None
        return data
