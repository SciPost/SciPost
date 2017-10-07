from django import forms

from .models import WorkLog


class WorkLogForm(forms.ModelForm):
    class Meta:
        model = WorkLog
        fields = (
            'comments',
            'duration',
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'})
        }
