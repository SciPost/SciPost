from django import forms

from .models import *
from .helpers import past_years

THESIS_ACTION_CHOICES = (
    (0, 'modify'),
    (1, 'accept'),
    (2, 'refuse (give reason below)'),
    )

THESIS_REFUSAL_CHOICES = (
    (0, '-'),
    (-1, 'a link to this thesis already exists'),
    (-2, 'the external link to this thesis does not work'),
    )


class RequestThesisLinkForm(forms.ModelForm):
    class Meta:
        model = ThesisLink
        fields = ['type', 'discipline', 'domain', 'subject_area',
                  'title', 'author', 'supervisor', 'institution',
                  'defense_date', 'pub_link', 'abstract']
        widgets = {
            'defense_date': forms.SelectDateWidget(years=past_years(50)),
            'pub_link': forms.TextInput(attrs={'placeholder': 'Full URL'})
        }


class VetThesisLinkForm(forms.Form):
    action_option = forms.ChoiceField(widget=forms.RadioSelect,
                                      choices=THESIS_ACTION_CHOICES,
                                      required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=THESIS_REFUSAL_CHOICES, required=False)
    email_response_field = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)


class ThesisLinkSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")
