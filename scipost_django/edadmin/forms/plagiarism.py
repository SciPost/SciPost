__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from submissions.models import (
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
)


class InternalPlagiarismAssessmentForm(forms.ModelForm):
    class Meta:
        model = InternalPlagiarismAssessment
        fields = [
            "submission",
            "status",
            "passed_on",
            "comments_for_edadmin",
            "comments_for_authors",
        ]


class iThenticatePlagiarismAssessmentForm(forms.ModelForm):
    class Meta:
        model = iThenticatePlagiarismAssessment
        fields = [
            "submission",
            "status",
            "passed_on",
            "comments_for_edadmin",
            "comments_for_authors",
        ]
