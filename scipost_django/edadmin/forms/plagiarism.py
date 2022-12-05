__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit

from submissions.models import (
    PlagiarismAssessment,
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
)


class PlagiarismAssessmentForm(forms.ModelForm):
    class Meta:
        model = PlagiarismAssessment
        fields = [
            "status",
            "comments_for_edadmin",
            "comments_for_authors",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("status"),
            Field("comments_for_edadmin"),
            Field("comments_for_authors"),
            ButtonHolder(Submit("submit", "Submit", css_class="btn btn-primary")),
        )

    def save(self):
        assessment = super().save(commit=False)
        if self.cleaned_data["status"] == self.instance.STATUS_PASSED:
            assessment.date_set = timezone.now()
        assessment.save()
        return assessment


class InternalPlagiarismAssessmentForm(PlagiarismAssessmentForm):
    class Meta:
        model = InternalPlagiarismAssessment
        fields = [
            "status",
            "comments_for_edadmin",
            "comments_for_authors",
        ]


class iThenticatePlagiarismAssessmentForm(PlagiarismAssessmentForm):
    class Meta:
        model = iThenticatePlagiarismAssessment
        fields = [
            "status",
            "comments_for_edadmin",
            "comments_for_authors",
        ]
