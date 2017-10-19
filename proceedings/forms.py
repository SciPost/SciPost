from django import forms

from .models import Proceedings


class ProceedingsForm(forms.ModelForm):
    class Meta:
        model = Proceedings
        fields = (
            'issue',
            'issue_name',
            'event_name',
            'event_description',
            'event_start_date',
            'event_end_date',
            'submissions_open',
            'submissions_deadline',
            'submissions_close',
        )
