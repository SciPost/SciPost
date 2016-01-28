from django import forms

from .models import *

from ratings.models import *

#class SubmissionForm(forms.Form):
#    submitted_to_journal = forms.ChoiceField(choices=SCIPOST_JOURNALS_SUBMIT, required=True, label='SciPost Journal to submit to:')
#    domain = forms.ChoiceField(choices=SCIPOST_JOURNALS_DOMAINS)
#    specialization = forms.ChoiceField(choices=SCIPOST_JOURNALS_SPECIALIZATIONS)
#    title = forms.CharField(max_length=300, required=True, label='Title')
#    author_list = forms.CharField(max_length=1000, required=True)
#    abstract = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols':60}), label='Abstract', required=True) # need TextField but doesn't exist
#    arxiv_link = forms.URLField(label='arXiv link (including version nr)', required=True)
class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submitted_to_journal', 'domain', 'specialization', 'title', 'author_list', 'abstract', 'arxiv_link']

    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)
        self.fields['arxiv_link'].widget.attrs.update({'placeholder': 'ex.:  arxiv.org/abs/1234.56789v1'})

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

#class ReportForm(forms.Form):
#    qualification = forms.ChoiceField(RATING_CHOICES, label='Your degree of qualification in assessing this Submission')
#    strengths = forms.CharField(widget=forms.Textarea(), required=False)
#    weaknesses = forms.CharField(widget=forms.Textarea(), required=False)
#    report = forms.CharField(widget=forms.Textarea(), required=False)
#    requested_changes = forms.CharField(widget=forms.Textarea(), required=False)
#    recommendation = forms.ChoiceField(choices=REPORT_REC)
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['qualification', 'strengths', 'weaknesses', 'report', 'requested_changes', 'recommendation']

class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=REPORT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)


