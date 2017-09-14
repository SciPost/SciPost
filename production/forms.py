from django import forms

from .models import ProductionUser, ProductionStream, ProductionEvent


class ProductionEventForm(forms.ModelForm):
    class Meta:
        model = ProductionEvent
        fields = (
            'event',
            'comments',
            'duration'
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'})
        }


class AssignOfficerForm(forms.ModelForm):
    officer = forms.ModelChoiceField(queryset=ProductionUser.objects.all())

    class Meta:
        model = ProductionStream
        fields = ()

    def clean_officer(self):
        officer = self.cleaned_data['officer']
        if officer in self.instance.officers.all():
            self.add_error('officer', 'Officer already assigned to Stream')
        return officer

    def save(self, commit=True):
        officer = self.cleaned_data['officer']
        self.instance.officers.add(officer)
        return self.instance


class UserToOfficerForm(forms.ModelForm):
    class Meta:
        model = ProductionUser
        fields = (
            'user',
        )
