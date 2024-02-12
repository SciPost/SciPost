__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit


class SubmissionAdmissionForm(forms.Form):
    choice = forms.ChoiceField(
        label="Admission of this Submission: pass to the Preassignment stage?",
        choices=(
            ("pass", "Pass"),
            ("fail", "Fail and email authors"),
        ),
        widget=forms.RadioSelect,
        required=True,
    )
    rejection_email_text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "For fail: message to be included in email for authors",
                "rows": 5,
                "cols": 80,
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rejection_email_text"].initial = (
            "In view of this, we are unable to proceed further with the handling of your manuscript. "
            "We hope you can easily find an alternative publishing venue. \n"
            "Despite this unsuccessful outcome, we thank you very much for your contribution, "
            "and hope to be able to be of service to you in the future."
        )
        self.fields["rejection_email_text"].help_text = (
            "The text that will be included in the email to the authors, "
            'after "We regret to inform you that your recent submission has not passed the admission step." '
            "Do *NOT* change the default if you don't wish to make changes."
        )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("choice"),
                    ButtonHolder(
                        Submit("submit", "Submit", css_class="btn btn-primary")
                    ),
                    css_class="col col-lg-4",
                ),
                Div(
                    Field("rejection_email_text"),
                    css_class="col col-lg-8",
                ),
                css_class="row",
            )
        )

    def clean(self):
        data = super().clean()
        if (
            self.cleaned_data["choice"] == "fail"
            and self.cleaned_data["rejection_email_text"] is None
        ):
            self.add_error(
                None, "Comments for authors must not be empty if marked as failed"
            )
