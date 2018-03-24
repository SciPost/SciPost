from django import forms

from .models import Funder, Grant

from scipost.forms import HttpRefererFormMixin
from scipost.models import Contributor


class FunderRegistrySearchForm(forms.Form):
    name = forms.CharField(max_length=128)


class FunderForm(forms.ModelForm):
    class Meta:
        model = Funder
        fields = ['name', 'acronym', 'identifier']


class FunderSelectForm(forms.Form):
    funder = forms.ModelChoiceField(queryset=Funder.objects.all())


class GrantForm(HttpRefererFormMixin, forms.ModelForm):
    class Meta:
        model = Grant
        fields = ['funder', 'number', 'recipient_name', 'recipient', 'further_details']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipient'] = forms.ModelChoiceField(
            queryset=Contributor.objects.select_related('user').order_by('user__last_name'),
            required=False)


class GrantSelectForm(forms.Form):
    grant = forms.ModelChoiceField(queryset=Grant.objects.all().select_related('funder'))
