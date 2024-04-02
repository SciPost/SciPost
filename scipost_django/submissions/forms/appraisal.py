__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, ButtonHolder, Button
from crispy_bootstrap5.bootstrap5 import FloatingField

from ethics.models import SubmissionClearance

from ..models import Qualification, Readiness


class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = [
            "submission",
            "fellow",
            "expertise_level",
            # "comments",
        ]
        widgets = {
            "submission": forms.HiddenInput(),
            "fellow": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["expertise_level"].label = (
            "Your expertise level for this Submission"
        )
        self.helper.layout = Layout(
            Field("submission"),
            Field("fellow"),
            FloatingField("expertise_level"),
        )


class ReadinessForm(forms.ModelForm):
    choice = forms.ChoiceField(
        choices=(
            [
                ("", "---------"),
                ("yes", "Yes, let me take charge now"),
            ]
            + list(Readiness.STATUS_CHOICES)
        ),
    )

    class Meta:
        model = Readiness
        fields = [
            "submission",
            "fellow",
            "choice",
        ]
        widgets = {
            "submission": forms.HiddenInput(),
            "fellow": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "instance" in kwargs and kwargs["instance"]:
            self.fields["choice"].initial = kwargs["instance"].status
        self.helper = FormHelper()
        self.fields["choice"].label = "Ready to take charge?"

        self.helper.layout = Layout(
            Field("submission"),
            Field("fellow"),
            FloatingField("choice"),
        )

    def save(self):
        instance = super().save(commit=False)
        # The "yes" choice must be handled separately in the view before calling save
        instance.status = self.cleaned_data["choice"]
        instance.save()
        return instance


class RadioAppraisalForm(forms.Form):
    """
    A collection of radios for the full appraisal of a submission.
    """

    expertise_level = forms.ChoiceField(
        label="Expertise level",
        choices=Qualification.EXPERTISE_LEVEL_CHOICES[1::2],  #! Hack: skip some choices
        widget=forms.RadioSelect(),
        required=False,
        initial=None,
    )
    readiness = forms.ChoiceField(
        label="Readiness",
        choices=(("assign_now", "Ready to take charge now"),)
        + Readiness.STATUS_CHOICES[0:1]
        + Readiness.STATUS_CHOICES[4:5],
        widget=forms.RadioSelect(),
        required=False,
        initial=None,
    )

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        self.fellow = kwargs.pop("fellow")

        super().__init__(*args, **kwargs)

        # Add any pre-existing choices to the form
        qualification = Qualification.objects.filter(
            submission=self.submission, fellow=self.fellow
        ).first()
        if qualification:
            if qualification.expertise_level not in dict(
                self.fields["expertise_level"].choices
            ):
                self.fields["expertise_level"].choices += (
                    (
                        qualification.expertise_level,
                        qualification.get_expertise_level_display(),
                    ),
                )

            self.initial["expertise_level"] = qualification.expertise_level

        readiness = Readiness.objects.filter(
            submission=self.submission, fellow=self.fellow
        ).first()
        if readiness:
            if readiness.status not in dict(self.fields["readiness"].choices):
                self.fields["readiness"].choices += (
                    (readiness.status, readiness.get_status_display()),
                )

            self.initial["readiness"] = readiness.status

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("readiness", id=f"{self.submission.id}-readiness"),
                    css_class="col-12 col-sm-6 col-md",
                ),
                Div(
                    Field("expertise_level", id=f"{self.submission.id}-expertise"),
                    css_class="col-12 col-sm-6 col-md",
                ),
                css_class="row mb-0",
            )
        )

    def clean(self):
        readiness = self.cleaned_data["readiness"]
        expertise_level = self.cleaned_data["expertise_level"]

        action = reason = None
        if not expertise_level:
            reason = "You must declare a level of expertise"
        elif not self.is_qualified:
            reason = "You must be at least marginally qualified"

        if readiness == "assign_now":
            action = "take charge"
        elif readiness == "desk_reject":
            action = "suggest a desk rejection"

        if action:  # If readiness is set to assign_now or desk_reject
            if reason:  # Both readiness and expertise_level are required
                self.add_error("expertise_level", f"{reason} to {action}.")
            if not self.has_clearance:  # If the fellow has no clearance
                self.add_error(
                    "readiness", f"You must declare no competing interests to {action}."
                )

    def save(self):
        """
        Create the individual Qualification and Readiness objects from the form data.
        """
        if expertise_level := self.cleaned_data["expertise_level"]:
            qualification, _ = Qualification.objects.get_or_create(
                submission=self.submission, fellow=self.fellow
            )
            print(expertise_level)
            qualification.expertise_level = expertise_level
            qualification.save()
            print(qualification)

        if (
            readiness_status := self.cleaned_data["readiness"]
        ) and readiness_status != "assign_now":
            readiness, _ = Readiness.objects.get_or_create(
                submission=self.submission, fellow=self.fellow
            )
            print(readiness_status)
            readiness.status = readiness_status
            readiness.save()
            print(readiness)

    @property
    def is_qualified(self):
        """
        Return True if the form data indicates that the fellow is qualified,
        i.e. has an expertise level in:
        - Expert
        - Very knowledgeable
        - Knowledgeable
        - Marginally qualified
        """

        is_qualified = self.cleaned_data["expertise_level"] in [
            choice[0] for choice in Qualification.EXPERTISE_LEVEL_CHOICES[:4]
        ]

        return is_qualified

    @property
    def has_clearance(self):
        """
        Returns True if the fellow has clearance (no Competing Interest) with the submission.
        """
        return SubmissionClearance.objects.filter(
            profile=self.fellow.contributor.profile,
            submission=self.submission,
        ).exists()

    def should_redirect_to_editorial_assignment(self):
        """
        Return True if the form data indicates that the fellow is ready to take charge now.
        """
        is_ready_to_take_charge = self.cleaned_data["readiness"] == "assign_now"
        return is_ready_to_take_charge and self.is_qualified and self.has_clearance
