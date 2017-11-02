from django import forms

from .models import Institute


class InstituteMergeForm(forms.ModelForm):
    institute = forms.ModelChoiceField(queryset=Institute.objects.none())

    class Meta:
        model = Institute
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institute'].queryset = Institute.objects.exclude(id=self.instance.id)

    def save(self, commit=True):
        old_institute = self.cleaned_data['institute']
        if commit:
            old_institute.contributors.update(institute=self.instance)
            old_institute.delete()
        return self.instance
