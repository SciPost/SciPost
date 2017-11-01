from django import forms

from .models import Affiliation


class AffiliationMergeForm(forms.ModelForm):
    affiliation = forms.ModelChoiceField(queryset=Affiliation.objects.none())

    class Meta:
        model = Affiliation
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['affiliation'].queryset = Affiliation.objects.exclude(id=self.instance.id)

    def save(self, commit=True):
        old_affiliation = self.cleaned_data['affiliation']
        if commit:
            old_affiliation.contributors.update(affiliation=self.instance)
            old_affiliation.delete()
        return self.instance
