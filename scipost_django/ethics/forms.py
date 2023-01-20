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
        }

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["related_profile"].label = "With which author?"
        self.fields["related_profile"].queryset = Profile.objects.filter(
            id__in=[ap.profile.id for ap in self.submission.author_profiles.all()]
        )
        self.fields["nature"].label = "Nature? You are/have..."
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
                    HTML("<em class='text-danger'>This Submission will not be visible to you anymore</em>"),
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
            )
        )
