from django import forms

from .models import ProductionEvent


class ProductionEventForm(forms.ModelForm):
    class Meta:
        model = ProductionEvent
        exclude = ['stream', 'noted_on', 'noted_by']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
            'duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'})
        }
