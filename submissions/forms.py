from django import forms
from django.core.validators import RegexValidator

from .constants import ASSIGNMENT_BOOL, ASSIGNMENT_REFUSAL_REASONS,\
                       REPORT_ACTION_CHOICES, REPORT_REFUSAL_CHOICES
from .models import Submission, RefereeInvitation, Report, EICRecommendation

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.models import Contributor

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, Submit


class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")


###############################
# Submission and resubmission #
###############################

class SubmissionIdentifierForm(forms.Form):
    identifier = forms.CharField(
        widget=forms.TextInput(
            {'label': 'arXiv identifier',
             'placeholder': 'new style (with version nr) ####.####(#)v#(#)',
             'cols': 20}
        ),
        validators=[
            RegexValidator(
                regex="^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$",
                message='The identifier you entered is improperly formatted '
                        '(did you forget the version number?)',
                code='invalid_identifier'
            ),
        ])


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['is_resubmission',
                  'discipline', 'submitted_to_journal', 'submission_type',
                  'domain', 'subject_area',
                  'secondary_areas',
                  'title', 'author_list', 'abstract',
                  'arxiv_identifier_w_vn_nr', 'arxiv_identifier_wo_vn_nr',
                  'arxiv_vn_nr', 'arxiv_link', 'metadata',
                  'author_comments', 'list_of_changes',
                  'remarks_for_editors',
                  'referees_suggested', 'referees_flagged']

    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)
        self.fields['is_resubmission'].widget = forms.HiddenInput()
        self.fields['arxiv_identifier_w_vn_nr'].widget = forms.HiddenInput()
        self.fields['arxiv_identifier_wo_vn_nr'].widget = forms.HiddenInput()
        self.fields['arxiv_vn_nr'].widget = forms.HiddenInput()
        self.fields['arxiv_link'].widget.attrs.update(
            {'placeholder': 'ex.:  arxiv.org/abs/1234.56789v1'})
        self.fields['metadata'].widget = forms.HiddenInput()
        self.fields['secondary_areas'].widget = forms.SelectMultiple(choices=SCIPOST_SUBJECT_AREAS)
        self.fields['abstract'].widget.attrs.update({'cols': 100})
        self.fields['author_comments'].widget.attrs.update({
            'placeholder': 'Your resubmission letter (will be viewable online)', })
        self.fields['list_of_changes'].widget.attrs.update({
            'placeholder': 'Give a point-by-point list of changes (will be viewable online)', })
        self.fields['remarks_for_editors'].widget.attrs.update({
            'placeholder': 'Any private remarks (for the editors only)', })
        self.fields['referees_suggested'].widget.attrs.update({
            'placeholder': 'Optional: names of suggested referees',
            'rows': 3})
        self.fields['referees_flagged'].widget.attrs.update({
            'placeholder': 'Optional: names of referees whose reports should be treated with caution (+ short reason)',
            'rows': 3})


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
    deadline = forms.DateField(required=False, label='',
                               widget=forms.SelectDateWidget)


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
        super(ReportForm, self).__init__(*args, **kwargs)
        self.fields['strengths'].widget.attrs.update(
            {'placeholder': 'Give a point-by-point (numbered 1-, 2-, ...) list of the paper\'s strengths',
             'rows': 10, 'cols': 100})
        self.fields['weaknesses'].widget.attrs.update(
            {'placeholder': 'Give a point-by-point (numbered 1-, 2-, ...) list of the paper\'s weaknesses',
             'rows': 10, 'cols': 100})
        self.fields['report'].widget.attrs.update({'placeholder': 'Your general remarks',
                                                   'rows': 10, 'cols': 100})
        self.fields['requested_changes'].widget.attrs.update(
            {'placeholder': 'Give a numbered (1-, 2-, ...) list of specifically requested changes',
             'cols': 100})


class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect,
                                      choices=REPORT_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(),
                                           label='Justification (optional)', required=False)

    def __init__(self, *args, **kwargs):
        super(VetReportForm, self).__init__(*args, **kwargs)
        self.fields['email_response_field'].widget.attrs.update(
            {'placeholder': 'Optional: give a textual justification (will be included in the email to the Report\'s author)',
             'rows': 5})


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
