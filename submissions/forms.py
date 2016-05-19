from django import forms
from django.contrib.auth.models import User, Group

from .models import *

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Fieldset, HTML, Submit


class SubmissionIdentifierForm(forms.Form):
    identifier = forms.CharField(widget=forms.TextInput({'label': 'arXiv identifier',
                                                         'placeholder': 'new style (with version nr) ####.####(#)v#(#)',
                                                         'cols': 20}))

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['discipline', 'submitted_to_journal', 'domain', 'specialization', 
                  'title', 'author_list', 'abstract', 'arxiv_link', 'metadata', 'referees_flagged']

    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)
        self.fields['arxiv_link'].widget.attrs.update({'placeholder': 'ex.:  arxiv.org/abs/1234.56789v1'})
        self.fields['metadata'].widget = forms.HiddenInput()
        self.fields['abstract'].widget.attrs.update({'cols': 100})
        self.fields['referees_flagged'].widget.attrs.update({
                'placeholder': 'Optional: names of referees whose reports should be treated with caution (+ short reason)',
                'rows': 3})


class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")


######################
# Editorial workflow #
######################

class AssignSubmissionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        discipline = kwargs.pop('discipline')
#        specialization = kwargs.pop('specialization') # Reactivate later on, once the Editorial College is large enough
        super(AssignSubmissionForm,self).__init__(*args, **kwargs)
        self.fields['editor_in_charge'] = forms.ModelChoiceField(
            queryset=Contributor.objects.filter(user__groups__name='Editorial College', 
                                                user__contributor__discipline=discipline, 
#                                                user__contributor__specializations__contains=[specialization,] # Reactivate later on, once the Editorial College is large enough
                                                ), required=True, label='Select an Editor-in-charge')


class ConsiderAssignmentForm(forms.Form):
    accept = forms.ChoiceField(widget=forms.RadioSelect, choices=ASSIGNMENT_BOOL, label="Are you willing to take charge of this Submission?")
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS, required=False)


class RefereeSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(RefereeSelectForm, self).__init__(*args, **kwargs)
        self.fields['last_name'].widget.attrs.update({'size': 20, 'placeholder': 'Search in contributors database'})

    last_name = forms.CharField()


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
            Div(Field('title'), Field('first_name'), Field('last_name'), Field('email_address'), 
                Submit('submit', 'Send invitation', css_class="submitButton"),
                css_class="flex-whitebox320")
            )


class ConsiderRefereeInvitationForm(forms.Form):
    accept = forms.ChoiceField(widget=forms.RadioSelect, choices=ASSIGNMENT_BOOL, label="Are you willing to referee this Submission?")
    refusal_reason = forms.ChoiceField(choices=ASSIGNMENT_REFUSAL_REASONS, required=False)


############
# Reports:
############

REPORT_ACTION_CHOICES = (
#    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse'),
    )

REPORT_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'unclear'),
    (-2, 'incorrect'),
    (-3, 'not useful'),
    (-4, 'not academic in style'),
    )

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['qualification', 'strengths', 'weaknesses', 'report', 'requested_changes', 
                  'validity', 'significance', 'originality', 'clarity', 'formatting', 'grammar', 
                  'recommendation', 'remarks_for_editors', 'anonymous']
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        self.fields['strengths'].widget.attrs.update({'placeholder': 'Give a point-by-point (numbered 1-, 2-, ...) list of the paper\'s strengths', 'rows': 10, 'cols': 100})
        self.fields['weaknesses'].widget.attrs.update({'placeholder': 'Give a point-by-point (numbered 1-, 2-, ...) list of the paper\'s weaknesses', 'rows': 10, 'cols': 100})
        self.fields['report'].widget.attrs.update({'placeholder': 'Your general remarks', 'rows': 10, 'cols': 100})
        self.fields['requested_changes'].widget.attrs.update({'placeholder': 'Give a numbered (1-, 2-, ...) list of specifically requested changes', 'cols': 100})


class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=REPORT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

    def __init__(self, *args, **kwargs):
        super(VetReportForm, self).__init__(*args, **kwargs)
        self.fields['email_response_field'].widget.attrs.update({'placeholder': 'Optional: give a textual justification (will be emailed to the Report\'s author)', 'rows': 3})


###################
# Communications #
###################

class EditorialCommunicationForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(), label='')

    def __init__(self, *args, **kwargs):
        super(EditorialCommunicationForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({'rows': 5, 'cols': 50, 'placeholder': 'Write your message in this box.'})



######################
# EIC Recommendation #
######################

class EICRecommendationForm(forms.ModelForm):
    class Meta:
        model = EICRecommendation
        fields = ['remarks_for_authors', 'requested_changes', 'recommendation', 'remarks_for_editorial_college']
    def __init__(self, *args, **kwargs):
        super(EICRecommendationForm, self).__init__(*args, **kwargs)
        self.fields['remarks_for_authors'].widget.attrs.update({'placeholder': 'Your general remarks for the authors', 'rows': 10, 'cols': 100})
        self.fields['requested_changes'].widget.attrs.update({'placeholder': 'If you request revisions, give a numbered (1-, 2-, ...) list of specifically requested changes', 'cols': 100})
        self.fields['remarks_for_editorial_college'].widget.attrs.update({'placeholder': 'If you recommend to accept or refuse, the Editorial College will vote; write any relevant remarks for the EC here.'})
