from django import forms

from .models import *


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['discipline', 'submitted_to_journal', 'domain', 'specialization', 'title', 'author_list', 'abstract', 'arxiv_link']

    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)
        self.fields['arxiv_link'].widget.attrs.update({'placeholder': 'ex.:  arxiv.org/abs/1234.56789v1'})
        self.fields['abstract'].widget.attrs.update({'cols': 100})

class ProcessSubmissionForm(forms.Form):
    editor_in_charge = forms.ModelChoiceField(queryset=Contributor.objects.filter(rank__gte=3), required=True, label='Select an Editor-in-charge')

class SubmissionSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author(s)")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")


############
# Reports:
############

REPORT_ACTION_CHOICES = (
#    (0, 'modify'), 
    (1, 'accept'), 
    (2, 'refuse (give reason below)'),
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
                  'recommendation']
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        self.fields['strengths'].widget.attrs.update({'placeholder': 'Give a point-by-point (numbered 1-, 2-, ...) list of the paper\'s strengths', 'rows': 10, 'cols': 100})
        self.fields['weaknesses'].widget.attrs.update({'placeholder': 'Give a point-by-point (numbered 1-, 2-, ...) list of the paper\'s weaknesses', 'rows': 10, 'cols': 100})
        self.fields['report'].widget.attrs.update({'placeholder': 'Your general remarks', 'rows': 10, 'cols': 100})
        self.fields['requested_changes'].widget.attrs.update({'placeholder': 'Give a numbered (1-, 2-, ...) list of specifically requested changes', 'cols': 100})


class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=REPORT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)


