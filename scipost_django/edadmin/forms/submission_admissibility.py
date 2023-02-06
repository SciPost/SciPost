__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit


class SubmissionAdmissibilityForm(forms.Form):
    admissibility = forms.ChoiceField(
        label="Can we proceed with consideration of this Submission?",
        choices=(
            ("pass", "Pass, carry on with plagiarism"),
            ("fail", "Fail: desk reject and email authors"),
        ),
        widget=forms.RadioSelect,
        required=True,
    )
    comments_for_authors = forms.CharField(
        widget=forms.Textarea(attrs={
            "placeholder": "For fail: message to be included in email for authors",
            "rows": 5,
            "cols": 80,
        }),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("admissibility"),
                    ButtonHolder(Submit("submit", "Submit", css_class="btn btn-primary")),
                    css_class="col col-lg-4",
                ),
                Div(
                    Field("comments_for_authors"),
                    css_class="col col-lg-8",
                ),
                css_class="row",
            )
        )

    def clean(self):
        data = super().clean()
        if (self.cleaned_data["admissibility"] == "fail" and
            self.cleaned_data["comments_for_authors"] is None):
            self.add_error(
                None,
                "Comments for authors must not be empty if marked as inadmissible"
            )
