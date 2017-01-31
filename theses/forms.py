from django import forms

from .models import *
from .helpers import past_years


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
    MODIFY = 0
    ACCEPT = 1
    REFUSE = 2
    THESIS_ACTION_CHOICES = (
        (MODIFY, 'modify'),
        (ACCEPT, 'accept'),
        (REFUSE, 'refuse (give reason below)'),
    )

    EMPTY_CHOICE = 0
    ALREADY_EXISTS = 1
    LINK_DOES_NOT_WORK = 2
    THESIS_REFUSAL_CHOICES = (
        (EMPTY_CHOICE, '---'),
        (ALREADY_EXISTS, 'a link to this thesis already exists'),
        (LINK_DOES_NOT_WORK, 'the external link to this thesis does not work'),
    )

    action_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=THESIS_ACTION_CHOICES, required=True, label='Action')
    refusal_reason = forms.ChoiceField(choices=THESIS_REFUSAL_CHOICES, required=False)
    justification = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 5, 'cols': 40}), label='Justification (optional)', required=False)

    def vet_request(self, thesis_link):
        print(self.cleaned_data)
        if self.cleaned_data['action_option'] == VetThesisLinkForm.ACCEPT:
            print('hoi')


class ThesisLinkSearchForm(forms.Form):
    author = forms.CharField(max_length=100, required=False, label="Author")
    title_keyword = forms.CharField(max_length=100, label="Title", required=False)
    abstract_keyword = forms.CharField(max_length=1000, required=False, label="Abstract")
    supervisor = forms.CharField(max_length=100, required=False, label="Supervisor")
