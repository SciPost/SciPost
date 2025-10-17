__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from crispy_bootstrap5.bootstrap5 import FloatingField

from ethics.models import SubmissionClearance
from submissions.models.assignment import ConditionalAssignmentOffer

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
        self.fields[
            "expertise_level"
        ].label = "Your expertise level for this Submission"
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
        + Readiness.STATUS_CHOICES[3:4]
        + Readiness.STATUS_CHOICES[5:6],
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

        # Disable the readiness field if the fellow made an assignment offer
        if self.submission.conditional_assignment_offers.filter(
            offered_by=self.fellow.contributor
        ).exists():
            self.fields["readiness"].disabled = True

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
        elif readiness == Readiness.STATUS_CONDITIONAL:
            action = "offer a conditional assignment"

            # Also check if the fellow has made an offer for conditional assignment
            offer = ConditionalAssignmentOffer.objects.filter(
                submission=self.submission,
                offered_by=self.fellow.contributor,
            )
            if not offer.exists():
                self.add_error(
                    "readiness",
                    "Please complete the form and make an offer for conditional assignment.",
                )

        if action:  # If readiness is set to assign_now or desk_reject
            if reason:  # Both readiness and expertise_level are required
                self.add_error("expertise_level", f"{reason} to {action}.")
            if not self.has_clearance:  # If the fellow has no clearance
                self.add_error(
                    "readiness",
                    f"You must declare no conflicts of interest to {action}.",
                )

    def save(self):
        """
        Create the individual Qualification and Readiness objects from the form data.
        """
        if expertise_level := self.cleaned_data["expertise_level"]:
            qualification, _ = Qualification.objects.get_or_create(
                submission=self.submission, fellow=self.fellow
            )
            qualification.expertise_level = expertise_level
            qualification.save()

        if (
            readiness_status := self.cleaned_data["readiness"]
        ) and readiness_status != "assign_now":
            readiness, _ = Readiness.objects.get_or_create(
                submission=self.submission, fellow=self.fellow
            )
            readiness.status = readiness_status
            readiness.save()

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
        return self.cleaned_data["expertise_level"] in Qualification.EXPERTISE_QUALIFIED

    @property
    def has_clearance(self):
        """
        Returns True if the fellow has clearance (no Conflict of Interest) with the submission.
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


class ConditionalAssignmentOfferInlineForm(forms.ModelForm):
    class Meta:
        model = ConditionalAssignmentOffer
        fields = ["submission", "offered_by", "condition_type"]
        widgets = {
            "submission": forms.HiddenInput(),
            "offered_by": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        self.offered_by = kwargs.pop("offered_by")
        self.readonly = kwargs.pop("readonly", False)

        # Create field depending on the type of condition
        extra_fields = {}

        condition_type = None
        if args and (data := args[0]) and data.get("condition_type"):
            condition_type = data.get("condition_type")
        elif instance := kwargs.get("instance"):
            condition_type = instance.condition_type
        elif len(ConditionalAssignmentOffer.CONDITION_CHOICES) == 1:
            condition_type = ConditionalAssignmentOffer.CONDITION_CHOICES[0][0]

        if condition_type == "JournalTransfer":
            alternative_journal_id = forms.ModelChoiceField(
                label="Alternative journal",
                queryset=self.submission.submitted_to.alternative_journals.all(),
            )
            extra_fields["alternative_journal_id"] = alternative_journal_id

        self.base_fields.update(extra_fields)
        super().__init__(*args, **kwargs)

        self.initial["submission"] = self.submission
        self.initial["offered_by"] = self.offered_by

        self.fields["condition_type"].label = "Condition for assignment"
        self.fields[
            "condition_type"
        ].choices = ConditionalAssignmentOffer.CONDITION_CHOICES

        # If the form is readonly, disable all fields
        for field in self.fields:
            if self.readonly:
                self.fields[field].disabled = True
            if field in extra_fields:
                self.initial[field] = self.instance.condition_details.get(field, None)
            else:
                self.initial[field] = getattr(self, field, None) or getattr(
                    self.instance, field, None
                )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("submission"),
            Field("offered_by"),
            Div(FloatingField("condition_type"), css_class="col"),
            *[Div(FloatingField(field), css_class="col") for field in extra_fields],
        )

    def clean(self):
        qualification = Qualification.objects.filter(
            submission=self.submission, fellow__contributor=self.offered_by
        ).first()
        has_clearance = SubmissionClearance.objects.filter(
            profile=self.offered_by.profile,
            submission=self.submission,
        ).exists()

        if qualification is None:
            self.add_error(
                None,
                "You must first declare your expertise level for this submission.",
            )
        elif not qualification.is_qualified:
            self.add_error(
                None,
                "You must be at least marginally qualified to make an assignment offer.",
            )
        if not has_clearance:
            self.add_error(
                None,
                "You must first declare no conflicts of interest with this submission.",
            )

        return super().clean()

    def save(self):
        instance = super().save(commit=False)

        # The readiness of the fellow must be set to conditional
        readiness, _ = Readiness.objects.get_or_create(
            submission=self.submission,
            fellow=self.offered_by.fellowships.active()
            .filter(college=self.submission.submitted_to.college)
            .first(),
        )
        readiness.status = Readiness.STATUS_CONDITIONAL
        readiness.save()

        if instance.condition_type == "JournalTransfer":
            instance.condition_details = {
                "alternative_journal_id": self.cleaned_data["alternative_journal_id"].id
            }

        instance.save()
        return instance
