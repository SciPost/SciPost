from django import forms

from .models import Proceedings


class ProceedingsForm(forms.ModelForm):
    class Meta:
        model = Proceedings
        fields = (
            'issue',
            'event_name',
            'event_suffix',
            'event_description',
            'event_start_date',
            'event_end_date',
            'submissions_open',
            'submissions_deadline',
            'submissions_close',
        )
