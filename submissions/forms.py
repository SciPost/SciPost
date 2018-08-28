__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import re

from django import forms
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .constants import (
    ASSIGNMENT_BOOL, ASSIGNMENT_REFUSAL_REASONS, STATUS_RESUBMITTED, REPORT_ACTION_CHOICES,
    REPORT_REFUSAL_CHOICES, STATUS_REJECTED, STATUS_INCOMING, REPORT_POST_EDREC, REPORT_NORMAL,
    STATUS_DRAFT, STATUS_UNVETTED, REPORT_ACTION_ACCEPT, REPORT_ACTION_REFUSE, STATUS_UNASSIGNED,
    EXPLICIT_REGEX_MANUSCRIPT_CONSTRAINTS, SUBMISSION_STATUS, PUT_TO_VOTING, CYCLE_UNDETERMINED,
    SUBMISSION_CYCLE_CHOICES, REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3, STATUS_VETTED,
    REPORT_MINOR_REV, REPORT_MAJOR_REV, REPORT_REJECT, STATUS_ACCEPTED, DECISION_FIXED, DEPRECATED,
    STATUS_EIC_ASSIGNED, CYCLE_DEFAULT, CYCLE_DIRECT_REC)
from . import exceptions, helpers
from .models import (
    Submission, RefereeInvitation, Report, EICRecommendation, EditorialAssignment,
    iThenticateReport, EditorialCommunication)
from .signals import notify_manuscript_accepted

from common.helpers import get_new_secrets_key
from colleges.models import Fellowship
from invitations.models import RegistrationInvitation
from journals.constants import SCIPOST_JOURNAL_PHYSICS_PROC, SCIPOST_JOURNAL_PHYSICS
from production.utils import get_or_create_production_stream
from scipost.constants import SCIPOST_SUBJECT_AREAS, INVITATION_REFEREEING
from scipost.services import ArxivCaller
from scipost.models import Contributor
import strings

import iThenticate


class SubmissionSearchForm(forms.Form):
    """Filter a Submission queryset using basic search fields."""

    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title = forms.CharField(max_length=100, required=False)
    abstract = forms.CharField(max_length=1000, required=False)
    subject_area = forms.CharField(max_length=10, required=False, widget=forms.Select(
                                   choices=((None, 'Show all'),) + SCIPOST_SUBJECT_AREAS[0][1]))

    def search_results(self):
        """Return all Submission objects according to search."""
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
            queryset = queryset.pool_editable(current_user).filter(
                status=self.cleaned_data['status'])
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
    """Mixin with checks run at least the Submission creation form."""

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
        """Check if previous submitted versions have the appropriate status."""
        identifiers = self.identifier_into_parts(identifier)
        submission = (Submission.objects
                      .filter(arxiv_identifier_wo_vn_nr=identifiers['arxiv_identifier_wo_vn_nr'])
                      .order_by('arxiv_vn_nr').last())

        # If submissions are found; check their statuses
        if submission:
            self.last_submission = submission
            if submission.open_for_resubmission:
                self.is_resubmission = True
                if self.requested_by.contributor not in submission.authors.all():
                    error_message = ('There exists a preprint with this arXiv identifier '
                                     'but an earlier version number. Resubmission is only possible'
                                     ' if you are a registered author of this manuscript.')
                    raise forms.ValidationError(error_message)
            elif submission.status == STATUS_REJECTED:
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
        """Check if arXiv identifier is valid for the Journal submitting to."""
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
        """Check if the Submission is a resubmission."""
        return self.is_resubmission

    def identifier_into_parts(self, identifier):
        """Split the arXiv identifier into parts."""
        data = {
            'arxiv_identifier_w_vn_nr': identifier,
            'arxiv_identifier_wo_vn_nr': identifier.rpartition('v')[0],
            'arxiv_vn_nr': int(identifier.rpartition('v')[2])
        }
        return data

    def do_pre_checks(self, identifier):
        """Group call of different checks."""
        self._submission_already_exists(identifier)
        self._call_arxiv(identifier)
        self._submission_is_already_published(identifier)
        self._submission_previous_version_is_valid_for_submission(identifier)


class SubmissionIdentifierForm(SubmissionChecks, forms.Form):
    """Prefill SubmissionForm using this form that takes an arXiv ID only."""

    IDENTIFIER_PATTERN_NEW = r'^[0-9]{4,}\.[0-9]{4,5}v[0-9]{1,2}$'
    IDENTIFIER_PLACEHOLDER = 'new style (with version nr) ####.####(#)v#(#)'

    identifier = forms.RegexField(regex=IDENTIFIER_PATTERN_NEW, strip=True,
                                  #   help_text=strings.arxiv_query_help_text,
                                  error_messages={'invalid': strings.arxiv_query_invalid},
                                  widget=forms.TextInput({'placeholder': IDENTIFIER_PLACEHOLDER}))

    def clean_identifier(self):
        """Do basic prechecks based on the arXiv ID only."""
        identifier = self.cleaned_data['identifier']
        self.do_pre_checks(identifier)
        return identifier

    def _gather_data_from_last_submission(self):
        """Return dictionary with data coming from previous submission version."""
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
        """Return dictionary to prefill `RequestSubmissionForm`."""
        form_data = self.arxiv_data
        form_data.update(self.identifier_into_parts(self.cleaned_data['identifier']))
        if self.submission_is_resubmission():
            form_data.update(self._gather_data_from_last_submission())
        return form_data


class RequestSubmissionForm(SubmissionChecks, forms.ModelForm):
    """Form to submit a new Submission."""

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
        self.fields['submission_type'].required = False
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
        """Check if author list matches the Contributor submitting.

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

    def clean_submission_type(self):
        """Validate Submission type.

        The SciPost Physics journal requires a Submission type to be specified.
        """
        submission_type = self.cleaned_data['submission_type']
        journal = self.cleaned_data['submitted_to_journal']
        if journal == SCIPOST_JOURNAL_PHYSICS and not submission_type:
            self.add_error('submission_type', 'Please specify the submission type.')
        return submission_type

    @transaction.atomic
    def copy_and_save_data_from_resubmission(self, submission):
        """Fill given Submission with data coming from last_submission."""
        if not self.last_submission:
            raise Submission.DoesNotExist

        # Close last submission
        Submission.objects.filter(id=self.last_submission.id).update(
            is_current=False, open_for_reporting=False, status=STATUS_RESUBMITTED)

        # Open for comment and reporting and copy EIC info
        Submission.objects.filter(id=submission.id).update(
            open_for_reporting=True,
            open_for_commenting=True,
            is_resubmission=True,
            visible_pool=True,
            editor_in_charge=self.last_submission.editor_in_charge,
            status=STATUS_EIC_ASSIGNED)

        # Add author(s) (claim) fields
        submission.authors.add(*self.last_submission.authors.all())
        submission.authors_claims.add(*self.last_submission.authors_claims.all())
        submission.authors_false_claims.add(*self.last_submission.authors_false_claims.all())

        # Create new EditorialAssigment for the current Editor-in-Charge
        EditorialAssignment.objects.create(
            submission=submission, to=self.last_submission.editor_in_charge, accepted=True)

    def set_pool(self, submission):
        """Set the default set of (guest) Fellows for this Submission."""
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
        """Fill, create and transfer data to the new Submission.

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

        if self.submission_is_resubmission():
            # Reset Refereeing Cycle. EIC needs to pick a cycle on resubmission.
            submission.refereeing_cycle = CYCLE_UNDETERMINED
            submission.save()  # Save before filling from old Submission.

            self.copy_and_save_data_from_resubmission(submission)
        else:
            # Save!
            submission.save()

        # Gather first known author and Fellows.
        submission.authors.add(self.requested_by.contributor)
        self.set_pool(submission)

        # Return latest version of the Submission. It could be outdated by now.
        return Submission.objects.get(id=submission.id)


class SubmissionReportsForm(forms.ModelForm):
    """Update refereeing pdf for Submission."""

    class Meta:
        model = Submission
        fields = ['pdf_refereeing_pack']


class SubmissionPrescreeningForm(forms.ModelForm):
    """Processing decision for pre-screening of Submission."""

    PASS = 'pass'
    CHOICES = ((PASS, 'Pass pre-screening. Proceed to the Pool.'),)
    decision = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES, required=False)

    class Meta:
        model = Submission
        fields = ()

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop('submission')
        super().__init__(*args, **kwargs)

    def clean(self):
        """Check if Submission has right status."""
        data = super().clean()
        if self.instance.status != STATUS_INCOMING:
            self.add_error(None, 'This Submission is currently not in pre-screening.')
        return data

    @transaction.atomic
    def save(self):
        """Update Submission status."""
        Submission.objects.filter(id=self.instance.id).update(
            status=STATUS_UNASSIGNED, visible_pool=True)


######################
# Editorial workflow #
######################

class InviteEditorialAssignmentForm(forms.ModelForm):
    """Invite new Fellow; create EditorialAssignment for Submission."""

    class Meta:
        model = EditorialAssignment
        fields = ('to',)
        labels = {
            'to': 'Fellow',
        }

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop('submission')
        super().__init__(*args, **kwargs)
        self.fields['to'].queryset = Contributor.objects.available().filter(
            fellowships__pool=self.submission).distinct().order_by('user__last_name')

    def save(self, commit=True):
        self.instance.submission = self.submission
        return super().save(commit)


class EditorialAssignmentForm(forms.ModelForm):
    """Create and/or process new EditorialAssignment for Submission."""

    DECISION_CHOICES = (
        ('accept', 'Accept'),
        ('decline', 'Decline'))
    CYCLE_CHOICES = (
        (CYCLE_DEFAULT, 'Normal refereeing cycle'),
        (CYCLE_DIRECT_REC, 'Directly formulate Editorial Recommendation for rejection'))

    decision = forms.ChoiceField(
        widget=forms.RadioSelect, choices=DECISION_CHOICES,
        label="Are you willing to take charge of this Submission?")
    refereeing_cycle = forms.ChoiceField(
        widget=forms.RadioSelect, choices=CYCLE_CHOICES, initial=CYCLE_DEFAULT)
    refusal_reason = forms.ChoiceField(
        choices=ASSIGNMENT_REFUSAL_REASONS)

    class Meta:
        model = EditorialAssignment
        fields = ()  # Don't use the default fields options because of the ordering of fields.

    def __init__(self, *args, **kwargs):
        """Add related submission as argument."""
        self.submission = kwargs.pop('submission')
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        if not self.instance.id:
            del self.fields['decision']
            del self.fields['refusal_reason']

    def has_accepted_invite(self):
        """Check if invite is accepted or if voluntered to become EIC."""
        return 'decision' not in self.cleaned_data or self.cleaned_data['decision'] == 'accept'

    def is_normal_cycle(self):
        """Check if normal refereeing cycle is chosen."""
        return self.cleaned_data['refereeing_cycle'] == CYCLE_DEFAULT

    def save(self, commit=True):
        """Save Submission to EditorialAssignment."""
        self.instance.submission = self.submission
        self.instance.date_answered = timezone.now()
        self.instance.to = self.request.user.contributor
        recommendation = super().save()  # Save already, in case it's a new recommendation.

        if self.has_accepted_invite():
            if self.is_normal_cycle():
                # Default Refereeing process!

                deadline = timezone.now() + datetime.timedelta(days=28)
                if recommendation.submission.submitted_to_journal == 'SciPostPhysLectNotes':
                    deadline += datetime.timedelta(days=28)

                # Update related Submission.
                Submission.objects.filter(id=self.submission.id).update(
                    refereeing_cycle=CYCLE_DEFAULT,
                    status=STATUS_EIC_ASSIGNED,
                    editor_in_charge=self.request.user.contributor,
                    reporting_deadline=deadline,
                    open_for_reporting=True,
                    open_for_commenting=True,
                    visible_public=True,
                    latest_activity=timezone.now())
            else:
                # Formulate rejection recommendation instead

                # Update related Submission.
                Submission.objects.filter(id=self.submission.id).update(
                    refereeing_cycle=CYCLE_DIRECT_REC,
                    status=STATUS_EIC_ASSIGNED,
                    editor_in_charge=self.request.user.contributor,
                    reporting_deadline=timezone.now(),
                    open_for_reporting=False,
                    open_for_commenting=True,
                    visible_public=False,
                    latest_activity=timezone.now())

        if self.has_accepted_invite():
            # Implicitly or explicity accept the assignment and deprecate others.
            recommendation.accepted = True
            EditorialAssignment.objects.filter(submission=self.submission, accepted=None).exclude(
                id=recommendation.id).update(deprecated=True)
        else:
            recommendation.accepted = False
            recommendation.refusal_reason = self.cleaned_data['refusal_reason']
        recommendation.save()  # Save again to register acceptance
        return recommendation


class ConsiderAssignmentForm(forms.Form):
    """Process open EditorialAssignment."""

    accept = forms.ChoiceField(widget=forms.RadioSelect, choices=ASSIGNMENT_BOOL,
                               label="Are you willing to take charge of this Submission?")
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS, required=False)


class RefereeSelectForm(forms.Form):
    """Pre-fill form to get the last name of the requested referee."""

    last_name = forms.CharField(widget=forms.TextInput({
        'placeholder': 'Search in contributors database'}))


class RefereeRecruitmentForm(forms.ModelForm):
    """Invite non-registered scientist to register and referee a Submission."""

    class Meta:
        model = RefereeInvitation
        fields = [
            'title',
            'first_name',
            'last_name',
            'email_address',
            'auto_reminders_allowed',
            'invitation_key']
        widgets = {
            'invitation_key': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.submission = kwargs.pop('submission', None)

        initial = kwargs.pop('initial', {})
        initial['invitation_key'] = get_new_secrets_key()
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_email_address(self):
        email = self.cleaned_data['email_address']
        if Contributor.objects.filter(user__email=email).exists():
            contr = Contributor.objects.get(user__email=email)
            msg = (
                'This email address is already registered. '
                'Invite {title} {last_name} using the link above.')
            self.add_error('email_address', msg.format(
                title=contr.get_title_display(), last_name=contr.user.last_name))
        return email

    def save(self, commit=True):
        if not self.request or not self.submission:
            raise forms.ValidationError('No request or Submission given.')

        self.instance.submission = self.submission
        self.instance.invited_by = self.request.user.contributor
        referee_invitation = super().save(commit=False)

        registration_invitation = RegistrationInvitation(
            title=referee_invitation.title,
            first_name=referee_invitation.first_name,
            last_name=referee_invitation.last_name,
            email=referee_invitation.email_address,
            invitation_type=INVITATION_REFEREEING,
            created_by=self.request.user,
            invited_by=self.request.user,
            invitation_key=referee_invitation.invitation_key,
            key_expires=timezone.now() + datetime.timedelta(days=365))

        if commit:
            referee_invitation.save()
            registration_invitation.save()
        return (referee_invitation, registration_invitation)


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
    """Assign Fellows to vote for EICRecommendation and open its status for voting."""

    eligible_fellows = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=True, label='Eligible for voting')

    class Meta:
        model = EICRecommendation
        fields = ()

    def __init__(self, *args, **kwargs):
        """Get queryset of Contributors eligibile for voting."""
        super().__init__(*args, **kwargs)
        self.fields['eligible_fellows'].queryset = Contributor.objects.filter(
            fellowships__pool=self.instance.submission).filter(
                Q(EIC=self.instance.submission) |
                Q(expertises__contains=[self.instance.submission.subject_area]) |
                Q(expertises__contains=self.instance.submission.secondary_areas)).order_by(
                    'user__last_name').distinct()

    def save(self, commit=True):
        """Update EICRecommendation status and save its voters."""
        self.instance.eligible_to_vote = self.cleaned_data['eligible_fellows']
        self.instance.status = PUT_TO_VOTING

        if commit:
            self.instance.save()
            self.instance.submission.touch()
            self.instance.voted_for.add(self.instance.submission.editor_in_charge)
        return self.instance


############
# Reports:
############

class ReportPDFForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['pdf_report']


class ReportForm(forms.ModelForm):
    """Write Report form."""

    report_type = REPORT_NORMAL

    class Meta:
        model = Report
        fields = ['qualification', 'strengths', 'weaknesses', 'report', 'requested_changes',
                  'validity', 'significance', 'originality', 'clarity', 'formatting', 'grammar',
                  'recommendation', 'remarks_for_editors', 'anonymous', 'file_attachment']

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            if kwargs['instance'].is_followup_report:
                # Prefill data from latest report in the series
                latest_report = kwargs['instance'].latest_report_from_thread()
                kwargs.update({
                    'initial': {
                        'qualification': latest_report.qualification,
                        'anonymous': latest_report.anonymous
                    }
                })

        self.submission = kwargs.pop('submission')

        super().__init__(*args, **kwargs)
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

        # Required fields on submission; optional on save as draft
        if 'save_submit' in self.data:
            required_fields = ['report', 'recommendation', 'qualification']
        else:
            required_fields = []
        required_fields_label = ['report', 'recommendation', 'qualification']

        # If the Report is not a followup: Explicitly assign more fields as being required!
        if not self.instance.is_followup_report:
            required_fields_label += [
                'strengths',
                'weaknesses',
                'requested_changes',
                'validity',
                'significance',
                'originality',
                'clarity',
                'formatting',
                'grammar']
            required_fields += [
                'strengths',
                'weaknesses',
                'requested_changes',
                'validity',
                'significance',
                'originality',
                'clarity',
                'formatting',
                'grammar']

        for field in required_fields:
            self.fields[field].required = True

        # Let user know the field is required!
        for field in required_fields_label:
            self.fields[field].label += ' *'

        if self.submission.eicrecommendations.active().exists():
            # An active EICRecommendation is already formulated. This Report will be flagged.
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
        # r = report.recommendation
        # t = report.qualification
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
        """Require a refusal reason if report is rejected."""
        reason = self.cleaned_data['refusal_reason']
        if self.cleaned_data['action_option'] == REPORT_ACTION_REFUSE:
            if not reason:
                self.add_error('refusal_reason', 'A reason must be given to refuse a report.')
        return reason

    def process_vetting(self, current_contributor):
        """Set the right report status and update submission fields if needed."""
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
    """Formulate an EICRecommendation."""

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
        """Accept two additional kwargs.

        -- submission: The Submission to formulate an EICRecommendation for.
        -- reformulate (bool): Reformulate the currently available EICRecommendations.
        """
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

    def save(self):
        recommendation = super().save(commit=False)
        recommendation.submission = self.submission
        recommendation.voting_deadline += datetime.timedelta(days=self.DAYS_TO_VOTE)  # Test this
        if self.reformulate:
            # Increment version number
            recommendation.version = len(self.earlier_recommendations) + 1
            event_text = 'The Editorial Recommendation has been reformulated: {}.'
        else:
            event_text = 'An Editorial Recommendation has been formulated: {}.'

        if recommendation.recommendation in [REPORT_MINOR_REV, REPORT_MAJOR_REV]:
            # Minor/Major revision: return to Author; ask to resubmit
            recommendation.status = DECISION_FIXED
            Submission.objects.filter(id=self.submission.id).update(open_for_reporting=False)

            # Add SubmissionEvents for both Author and EIC
            self.submission.add_general_event(event_text.format(
                recommendation.get_recommendation_display()))
        else:
            # Add SubmissionEvent for EIC only
            self.submission.add_event_for_eic(event_text.format(
                recommendation.get_recommendation_display()))

        if self.earlier_recommendations:
            self.earlier_recommendations.update(active=False, status=DEPRECATED)

            # All reports already submitted are now formulated *after* eic rec formulation
            Report.objects.filter(
                submission__eicrecommendations__in=self.earlier_recommendations).update(
                    report_type=REPORT_NORMAL)

        recommendation.save()

        if self.assignment:
            # The EIC has fulfilled this editorial assignment.
            self.assignment.completed = True
            self.assignment.save()
        return recommendation

    def revision_requested(self):
        return self.instance.recommendation in [REPORT_MINOR_REV, REPORT_MAJOR_REV]

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
        """Load and save EICRecommendations related to Submission of the instance."""
        self.earlier_recommendations = self.submission.eicrecommendations.all()


###############
# Vote form #
###############

class RecommendationVoteForm(forms.Form):
    """Cast vote on EICRecommendation form."""

    vote = forms.ChoiceField(
        widget=forms.RadioSelect, choices=[
            ('agree', 'Agree'), ('disagree', 'Disagree'), ('abstain', 'Abstain')])
    remark = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3,
        'cols': 30,
        'placeholder': 'Your remark (optional)'
    }), label='', required=False)


class SubmissionCycleChoiceForm(forms.ModelForm):
    """Make a decision on the Submission's cycle and make publicly available."""

    referees_reinvite = forms.ModelMultipleChoiceField(
        queryset=RefereeInvitation.objects.none(),
        widget=forms.CheckboxSelectMultiple({'checked': 'checked'}),
        required=False, label='Reinvite referees')

    class Meta:
        model = Submission
        fields = ('refereeing_cycle',)
        widgets = {'refereeing_cycle': forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        """Update choices and queryset."""
        super().__init__(*args, **kwargs)
        self.fields['refereeing_cycle'].choices = SUBMISSION_CYCLE_CHOICES
        other_submissions = self.instance.other_versions.all()
        if other_submissions:
            self.fields['referees_reinvite'].queryset = RefereeInvitation.objects.filter(
                submission__in=other_submissions).distinct()

    def save(self):
        """Make Submission publicly available after decision."""
        self.instance.visible_public = True
        return super().save()


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
                self.add_error(
                    None, 'The pdf could not be found at arXiv. Please upload the pdf manually.')
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
            try:
                self.response = self.call_ithenticate()
            except AttributeError:
                if not self.fields.get('file'):
                    # The document is invalid.
                    self.add_error(None, ('A valid pdf could not be found at arXiv.'
                                          ' Please upload the pdf manually.'))
                else:
                    self.add_error(None, ('The uploaded file is not valid.'
                                          ' Please upload a valid pdf.'))
                self.fields['file'] = forms.FileField()
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
            Submission.objects.filter(id=self.submission.id).update(plagiarism_report=report)
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


class FixCollegeDecisionForm(forms.ModelForm):
    """Fix EICRecommendation decision."""

    FIX, DEPRECATE = 'fix', 'deprecate'
    action = forms.ChoiceField(choices=((FIX, FIX), (DEPRECATE, DEPRECATE)))

    class Meta:
        model = EICRecommendation
        fields = ()

    def __init__(self, *args, **kwargs):
        """Accept request as argument."""
        self.submission = kwargs.pop('submission', None)
        self.request = kwargs.pop('request', None)
        return super().__init__(*args, **kwargs)

    def clean(self):
        """Check if EICRecommendation has the right decision."""
        data = super().clean()
        if self.instance.status == DECISION_FIXED:
            self.add_error(None, 'This EICRecommendation is already fixed.')
        elif self.instance.status == DEPRECATED:
            self.add_error(None, 'This EICRecommendation is deprecated.')
        return data

    def is_fixed(self):
        """Check if decision is fixed."""
        return self.cleaned_data['action'] == self.FIX

    def fix_decision(self, recommendation):
        """Fix decision of EICRecommendation."""
        EICRecommendation.objects.filter(id=recommendation.id).update(status=DECISION_FIXED)
        submission = recommendation.submission
        if recommendation.recommendation in [REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3]:
            # Publish as Tier I, II or III
            Submission.objects.filter(id=submission.id).update(
                visible_public=True, status=STATUS_ACCEPTED, acceptance_date=datetime.date.today(),
                latest_activity=timezone.now())

            # Start a new ProductionStream
            get_or_create_production_stream(submission)

            if self.request:
                # Add SubmissionEvent for authors
                notify_manuscript_accepted(self.request.user, submission, False)
        elif recommendation.recommendation == REPORT_REJECT:
            # Decision: Rejection. Auto hide from public and Pool.
            Submission.objects.filter(id=submission.id).update(
                visible_public=False, visible_pool=False,
                status=STATUS_REJECTED, latest_activity=timezone.now())
            submission.get_other_versions().update(visible_public=False)

        # Add SubmissionEvent for authors
        submission.add_event_for_author(
            'The Editorial Recommendation has been formulated: {0}.'.format(
                recommendation.get_recommendation_display()))
        submission.add_event_for_eic(
            'The Editorial Recommendation has been fixed: {0}.'.format(
                recommendation.get_recommendation_display()))
        return recommendation

    def deprecate_decision(self, recommendation):
        """Deprecate decision of EICRecommendation."""
        EICRecommendation.objects.filter(id=recommendation.id).update(
            status=DEPRECATED, active=False)
        recommendation.submission.add_event_for_eic(
            'The Editorial Recommendation (version {version}) has been deprecated: {decision}.'.format(
                version=recommendation.version,
                decision=recommendation.get_recommendation_display()))

        return recommendation

    def save(self):
        """Update EICRecommendation and related Submission."""
        if self.is_fixed():
            return self.fix_decision(self.instance)
        elif self.cleaned_data['action'] == self.DEPRECATE:
            return self.deprecate_decision(self.instance)
        else:
            raise ValueError('The decision given is invalid')
        return self.instance
