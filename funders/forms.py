from django import forms

from .models import Funder, Grant

from scipost.models import Contributor


class FunderRegistrySearchForm(forms.Form):
    name = forms.CharField(max_length=128)


class FunderForm(forms.ModelForm):
    class Meta:
        model = Funder
        fields = ['name', 'acronym', 'identifier',]


class GrantForm(forms.ModelForm):
    class Meta:
        model = Grant
        fields = ['funder', 'number', 'recipient_name', 'recipient',]

    def __init__(self, *args, **kwargs):
        super(GrantForm, self).__init__(*args, **kwargs)
        self.fields['recipient'] = forms.ModelChoiceField(
            queryset=Contributor.objects.all().order_by('user__last_name'))


class GrantSelectForm(forms.Form):
    grant = forms.ModelChoiceField(queryset=Grant.objects.all())
