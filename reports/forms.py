from django import forms

from .models import *

from ratings.models import *

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



class ReportForm(forms.Form):
    qualification = forms.ChoiceField(RATING_CHOICES, label='Your degree of qualification in assessing this Submission')
    strengths = forms.CharField(widget=forms.Textarea(), required=False)
    weaknesses = forms.CharField(widget=forms.Textarea(), required=False)
    report = forms.CharField(widget=forms.Textarea(), required=False)
    requested_changes = forms.CharField(widget=forms.Textarea(), required=False)
    recommendation = forms.ChoiceField(choices=REPORT_REC)

class VetReportForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect, choices=REPORT_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=REPORT_REFUSAL_CHOICES)
    email_response_field = forms.CharField(widget=forms.Textarea(), label='Justification (optional)', required=False)

