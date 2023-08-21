__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from scipost.fields import ReCaptchaField
from .models import JobOpening, JobApplication


class JobOpeningForm(forms.ModelForm):
    class Meta:
        model = JobOpening
        fields = [
            "slug",
            "announced",
            "title",
            "short_description",
            "description",
            "application_deadline",
            "status",
        ]
        widgets = {
            "announced": forms.DateInput(attrs={"type": "date"}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
        }


class JobApplicationForm(forms.ModelForm):
    captcha = ReCaptchaField(label="* Please verify to continue:")

    class Meta:
        model = JobApplication
        fields = [
            "status",
            "jobopening",
            "date_received",
            "title",
            "first_name",
            "last_name",
            "email",
            "motivation",
            "cv",
        ]
        widgets = {
            "announced": forms.DateInput(attrs={"type": "date"}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget = forms.HiddenInput()
        self.fields["date_received"].widget = forms.HiddenInput()
        self.fields["jobopening"].widget = forms.HiddenInput()
        self.fields["cv"].label = "CV"
