__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.db.models import Q, QuerySet
from django.utils.html import format_html

from common.forms import CrispyFormMixin, SearchForm

from .models import ConflictOfInterest, GenAIDisclosure

from profiles.models import Profile


class ConflictSearchForm(CrispyFormMixin, SearchForm[ConflictOfInterest]):
    model = ConflictOfInterest
    queryset = ConflictOfInterest.objects.all()

    name = forms.CharField(label="Name", required=False)
    nature = forms.ChoiceField(
        label="Nature",
        choices=((None, "Any"),) + ConflictOfInterest.NATURE_CHOICES,
        required=False,
    )
    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("nature", "Nature"),
            ("profile__last_name", "Name"),
            ("related_profile__last_name", "Related name"),
            ("declared_on", "Declared on"),
            ("date_expiry", "Expiration date"),
            ("date_from", "Date from"),
            ("date_until", "Date until"),
        ),
        required=False,
        initial="declared_on",
    )

    def get_form_layout(self) -> Layout:
        return Layout(
            Div(
                Div(FloatingField("name"), css_class="col"),
                Div(FloatingField("nature"), css_class="col-auto"),
                Div(FloatingField("orderby"), css_class="col-auto"),
                Div(FloatingField("ordering"), css_class="col-auto"),
                css_class="row mb-0",
            ),
        )

    def filter_queryset(
        self, queryset: "QuerySet[ConflictOfInterest]"
    ) -> "QuerySet[ConflictOfInterest]":

        queryset = queryset.annot_is_applicable()

        if nature := self.cleaned_data.get("nature"):
            queryset = queryset.filter(nature=nature)

        if name := self.cleaned_data.get("name"):
            queryset = queryset.filter(
                Q(profile__full_name__unaccent__icontains=name)
                | Q(related_profile__full_name__unaccent__icontains=name)
            )

        return queryset


class SubmissionConflictOfInterestForm(forms.ModelForm):
    class Meta:
        model = ConflictOfInterest
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
                HTML(
                    """<span class="text-primary me-2">{% include 'bi/exclamation-circle-fill.html' %}</span>
                    When declaring a "Coauthor" relationship, please use the last day of the collaboration
                    as the "Date From" field and leave the "Date Until" field blank.
                    """
                ),
                css_class="bg-primary bg-opacity-10 p-2 mb-2 rounded",
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


class SubmissionConflictOfInterestTableRowForm(SubmissionConflictOfInterestForm):
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


class GenAIDisclosureForm(forms.ModelForm):
    was_used = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[
            (
                False,
                format_html(
                    "I declare that <strong>no</strong> generative AI tool has been used "
                    "at any step in the preparation of this content."
                ),
            ),
            (
                True,
                "I declare that generative AI tools have been used in the preparation of this content.",
            ),
        ],
        label="Generative AI disclosure",
        required=True,
    )
    use_details = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Generative AI tool usage details",
        help_text="Please specify which generative AI tools were used "
        "(including their version numbers or date of use), "
        "in which parts, and for which purposes.",
        required=False,
    )

    class Media:
        js = ("ethics/gen_ai_disclosure_form_selector.js",)

    class Meta:
        model = GenAIDisclosure
        fields = ["was_used", "use_details"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(Field("was_used"), css_class="col-12"),
                Div(Field("use_details"), css_class="col-12"),
                css_class="row mb-0",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        was_used = cleaned_data.get("was_used") == "True"
        use_details = cleaned_data.get("use_details")

        if was_used and not use_details:
            self.add_error(
                "use_details",
                "Please provide details on the generative AI tools used.",
            )

        return cleaned_data

    def save(self, commit=True, *args, **kwargs) -> GenAIDisclosure:
        gen_ai_disclosure = super().save(commit=False)
        for kwarg in kwargs:
            setattr(gen_ai_disclosure, kwarg, kwargs[kwarg])
        if commit:
            gen_ai_disclosure.save()
        return gen_ai_disclosure


class GenAIDisclosureAppendageForm(GenAIDisclosureForm):
    """
    This form is used to append a new statement to an existing GenAIDisclosure's
    `use_details` field, while keeping the original declaration intact.
    """

    new_details = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Additional generative AI tool usage details",
        help_text="Please optionally specify additional generative AI tools used "
        "in this version to be included alongside the original declaration.",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        previous_disclosure = kwargs.pop("previous_disclosure", None)
        if previous_disclosure:
            kwargs["initial"] = {
                "was_used": previous_disclosure.was_used,
                "use_details": previous_disclosure.use_details,
            } | kwargs.get("initial", {})

        super().__init__(*args, **kwargs)

        self.fields["was_used"].disabled = True
        self.fields["use_details"].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(Field("was_used"), css_class="col-12"),
                Div(Field("use_details"), css_class="col-12"),
                Div(Field("new_details"), css_class="col-12"),
                css_class="row mb-0",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        cleaned_data["use_details"] = (
            cleaned_data.get("use_details", "")
            + "\n"
            + cleaned_data.get("new_details", "")
        ).strip()

        return cleaned_data
