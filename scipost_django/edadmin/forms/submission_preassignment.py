__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit


class SubmissionPreassignmentDecisionForm(forms.Form):
    choice = forms.ChoiceField(
        label="Preassignment done? Pass to the Assignment stage?",
        choices=(
            ("pass", "Pass"),
            ("fail", "Fail and email authors"),
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
                    Field("choice"),
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
        if (self.cleaned_data["choice"] == "fail" and
            self.cleaned_data["comments_for_authors"] is None):
            self.add_error(
                None,
                "Comments for authors must not be empty if marked as failed"
            )
