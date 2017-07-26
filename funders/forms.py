from django import forms

from .models import Funder, Grant

class FunderRegistrySearchForm(forms.Form):
    name = forms.CharField(max_length=128)


class FunderForm(forms.ModelForm):
    class Meta:
        model = Funder
        fields = ['name', 'identifier',]


class GrantForm(forms.ModelForm):
    class Meta:
        model = Grant
        fields = ['funder', 'number', 'recipient_name', 'recipient',]


class GrantSelectForm(forms.Form):
    grant = forms.ModelChoiceField(queryset=Grant.objects.all())
