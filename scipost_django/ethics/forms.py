__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField

from .models import CompetingInterest

from profiles.models import Profile


class SubmissionCompetingInterestForm(forms.ModelForm):
    class Meta:
        model = CompetingInterest
        fields = [
            "profile",
            "related_profile",
            "nature",
            "date_from",
            "date_until",
            "declared_by",
            # "comments",
        ]
        widgets = {
            "profile": forms.HiddenInput(),
            "declared_by": forms.HiddenInput(),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_until": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)
        self.fields["related_profile"].label = "With which author?"
        self.fields["related_profile"].queryset = Profile.objects.filter(
            id__in=[ap.profile.id for ap in self.submission.author_profiles.all()]
        )
        self.fields["nature"].label = "Nature? You are/have..."
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("related_profile"), css_class="col-lg-6"),
                Div(Field("nature"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(Field("date_from"), css_class="col-lg-6"),
                Div(Field("date_until"), css_class="col-lg-6"),
                css_class="row mb-0",
            ),
            Div(
                Div(
                    Field("profile"),
                    Field("declared_by"),
                    HTML(
                        "<em class='text-danger'>This Submission will not be visible to you anymore</em>"
                    ),
                    css_class="col-lg-6",
                ),
                Div(
                    ButtonHolder(
                        Submit(
                            "submit",
                            "Submit",
                            css_class="btn btn-danger mt-auto",
                        )
                    ),
                    css_class="col-lg-6",
                ),
                css_class="row",
            ),
        )


class SubmissionCompetingInterestTableRowForm(SubmissionCompetingInterestForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["profile"].widget = forms.Select(
            choices=[(self.initial["profile"].id, str(self.initial["profile"]))],
        )
        self.fields["declared_by"].widget = forms.Select(
            choices=(
                list(self.fields["related_profile"].choices)
                + [(self.initial["profile"].id, str(self.initial["profile"]))]
                + [(self.initial["declared_by"].id, str(self.initial["declared_by"]))]
            ),
        )
        self.helper.layout = Layout(
            Div(
                FloatingField("profile", wrapper_class="mb-0"),
                FloatingField("related_profile", wrapper_class="mb-0"),
                FloatingField("nature", wrapper_class="mb-0"),
                FloatingField("date_from", wrapper_class="mb-0"),
                FloatingField("date_until", wrapper_class="mb-0"),
                FloatingField("declared_by", wrapper_class="mb-0"),
                ButtonHolder(Submit("submit", "Declare")),
                css_class="d-flex justify-content-between align-items-center",
            )
        )

        self.fields["related_profile"].label = "Submission author"
        self.fields["nature"].label = "Nature"
