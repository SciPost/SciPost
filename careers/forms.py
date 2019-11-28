__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from .models import JobOpening


class JobOpeningForm(forms.Form):

    class Meta:
        model = JobOpening
        fields = [
            'slug',
            'announced',
            'title',
            'description',
            'application_deadline',
            'status'
        ]
