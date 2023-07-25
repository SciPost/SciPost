__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms
from django.db.models import Q

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from ontology.models import Specialty
from proceedings.models import Proceedings
from profiles.models import Profile
from submissions.models import Submission
from scipost.forms import RequestFormMixin
from scipost.models import Contributor

from .models import (
    College,
    Fellowship,
    PotentialFellowship,
    PotentialFellowshipEvent,
    FellowshipNomination,
    FellowshipNominationComment,
    FellowshipNominationDecision,
    FellowshipInvitation,
)
from .constants import (
    POTENTIAL_FELLOWSHIP_IDENTIFIED,
    POTENTIAL_FELLOWSHIP_NOMINATED,
    POTENTIAL_FELLOWSHIP_EVENT_DEFINED,
    POTENTIAL_FELLOWSHIP_EVENT_NOMINATED,
)
from .utils import check_profile_eligibility_for_fellowship


class CollegeChoiceForm(forms.Form):
    college = forms.ModelChoiceField(queryset=College.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                FloatingField("college"),
            )
        )


class FellowshipSearchForm(forms.Form):
    college = forms.ModelChoiceField(
        queryset=College.objects.all(),
        widget=forms.HiddenInput(),
    )
    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.all(),
        label="Specialty",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "initial" in kwargs:
            self.fields["specialty"].queryset = Specialty.objects.filter(
                acad_field=kwargs["initial"].get("college").acad_field
            )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                FloatingField("college"),
            ),
            Div(
                FloatingField("specialty"),
            ),
        )

    def search_results(self):
        fellowships = Fellowship.objects.active()
        if self.initial and self.initial.get("college", None):
            fellowships = fellowships.filter(college=self.initial["college"])
        if hasattr(self, "cleaned_data"):
            if self.cleaned_data.get("college"):
                fellowships = fellowships.filter(
                    college=self.cleaned_data.get("college")
                )
            if self.cleaned_data.get("specialty"):
                fellowships = fellowships.filter(
                    contributor__profile__specialties__in=[
                        self.cleaned_data.get("specialty"),
                    ]
                )
        return fellowships


class FellowshipSelectForm(forms.Form):
    fellowship = forms.ModelChoiceField(
        queryset=Fellowship.objects.all(),
        widget=autocomplete.ModelSelect2(url="/colleges/fellowship-autocomplete"),
        help_text=("Start typing, and select from the popup."),
    )


class FellowshipDynSelForm(forms.Form):
    q = forms.CharField(max_length=32, label="Search (by name)")
    action_url_name = forms.CharField()
    action_url_base_kwargs = forms.JSONField(required=False)
    action_target_element_id = forms.CharField()
    action_target_swap = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("q", autocomplete="off"),
            Field("action_url_name", type="hidden"),
            Field("action_url_base_kwargs", type="hidden"),
            Field("action_target_element_id", type="hidden"),
            Field("action_target_swap", type="hidden"),
        )

    def search_results(self):
        if self.cleaned_data["q"]:
            fellowships = Fellowship.objects.filter(
                Q(contributor__profile__last_name__icontains=self.cleaned_data["q"])
                | Q(contributor__profile__first_name__icontains=self.cleaned_data["q"])
            ).distinct()
            return fellowships
        else:
            return Fellowship.objects.none()


class FellowshipForm(forms.ModelForm):
    class Meta:
        model = Fellowship
        fields = (
            "college",
            "contributor",
            "start_date",
            "until_date",
            "status",
        )
        help_texts = {
            "status": "[select if this is a regular, senior or guest Fellowship]"
        }
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "until_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contributor"].disabled = True

    def clean(self):
        super().clean()
        start = self.cleaned_data.get("start_date")
        until = self.cleaned_data.get("until_date")
        if start and until:
            if until <= start:
                self.add_error(
                    "until_date", "The given dates are not in chronological order."
                )


class FellowshipTerminateForm(forms.ModelForm):
    class Meta:
        model = Fellowship
        fields = []

    def save(self):
        today = datetime.date.today()
        fellowship = self.instance
        if not fellowship.until_date or fellowship.until_date > today:
            fellowship.until_date = today
        return fellowship.save()


class FellowshipRemoveSubmissionForm(forms.ModelForm):
    """
    Use this form in admin-accessible views only! It could possibly reveal the
    identity of the Editor-in-charge!
    """

    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop("submission")
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.submission.editor_in_charge == self.instance.contributor:
            self.add_error(
                None,
                (
                    "Submission cannot be removed as the Fellow is"
                    " Editor-in-charge of this Submission."
                ),
            )

    def save(self):
        fellowship = self.instance
        fellowship.pool.remove(self.submission)
        return fellowship


class FellowshipAddSubmissionForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.none(),
        empty_label="Please choose the Submission to add to the pool",
    )

    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pool = self.instance.pool.values_list("id", flat=True)
        self.fields["submission"].queryset = Submission.objects.exclude(id__in=pool)

    def save(self):
        submission = self.cleaned_data["submission"]
        fellowship = self.instance
        fellowship.pool.add(submission)
        return fellowship


class SubmissionAddFellowshipForm(forms.ModelForm):
    fellowship = forms.ModelChoiceField(
        queryset=None,
        to_field_name="id",
        empty_label="Please choose the Fellow to add to this Submission's Fellowship",
    )

    class Meta:
        model = Submission
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pool = self.instance.fellows.values_list("id", flat=True)
        self.fields["fellowship"].label = ""
        self.fields["fellowship"].queryset = (
            Fellowship.objects.active()
            .filter(college=self.instance.submitted_to.college)
            .exclude(id__in=pool)
        )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("fellowship"), css_class="col-lg-6"),
                Div(
                    Submit(
                        "submit",
                        "Add",
                    ),
                    css_class="col-lg-6",
                ),
                css_class="row",
            )
        )

    def save(self):
        fellowship = self.cleaned_data["fellowship"]
        submission = self.instance
        submission.fellows.add(fellowship)
        return submission


class FellowshipRemoveProceedingsForm(forms.ModelForm):
    """
    Use this form in admin-accessible views only! It could possibly reveal the
    identity of the Editor-in-charge!
    """

    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        self.proceedings = kwargs.pop("proceedings")
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.proceedings.lead_fellow == self.instance:
            self.add_error(
                None, "Fellowship cannot be removed as it is assigned as lead fellow."
            )

    def save(self):
        fellowship = self.instance
        self.proceedings.fellowships.remove(fellowship)
        return fellowship


class FellowshipAddProceedingsForm(forms.ModelForm):
    proceedings = forms.ModelChoiceField(
        queryset=None,
        to_field_name="id",
        empty_label="Please choose the Proceedings to add to the Pool",
    )

    class Meta:
        model = Fellowship
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        proceedings = self.instance.proceedings.values_list("id", flat=True)
        self.fields["proceedings"].queryset = Proceedings.objects.exclude(
            id__in=proceedings
        )

    def save(self):
        proceedings = self.cleaned_data["proceedings"]
        fellowship = self.instance
        proceedings.fellowships.add(fellowship)
        return fellowship


class PotentialFellowshipForm(RequestFormMixin, forms.ModelForm):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.all(),
        widget=autocomplete.ModelSelect2(url="/profiles/profile-autocomplete"),
    )

    class Meta:
        model = PotentialFellowship
        fields = ["college", "profile"]

    def clean_profile(self):
        """Check that no preexisting PotentialFellowship exists."""
        cleaned_profile = self.cleaned_data["profile"]
        if cleaned_profile.potentialfellowship_set.all():
            self.add_error(
                "profile",
                "This profile already has a PotentialFellowship. Update that instead.",
            )
        return cleaned_profile

    def save(self):
        """
        The default status is IDENTIFIED, which is appropriate
        if the PotentialFellow was added directly by SciPost Admin.
        But if the PotFel is nominated by somebody on the Advisory Board
        or by an existing Fellow, the status is set to NOMINATED and
        the person nominating is added to the list of in_agreement with election.
        """
        potfel = super().save()
        nominated = self.request.user.groups.filter(
            name__in=["Advisory Board", "Editorial College"]
        ).exists()
        if nominated:
            potfel.status = POTENTIAL_FELLOWSHIP_NOMINATED
            # If user is Senior Fellow for that College, auto-add Agree vote
            if (
                self.request.user.contributor.fellowships.senior()
                .filter(college=potfel.college)
                .exists()
            ):
                potfel.in_agreement.add(self.request.user.contributor)
            event = POTENTIAL_FELLOWSHIP_EVENT_NOMINATED
        else:
            potfel.status = POTENTIAL_FELLOWSHIP_IDENTIFIED
            event = POTENTIAL_FELLOWSHIP_EVENT_DEFINED
        potfel.save()
        newevent = PotentialFellowshipEvent(
            potfel=potfel, event=event, noted_by=self.request.user.contributor
        )
        newevent.save()
        return potfel


class PotentialFellowshipStatusForm(forms.ModelForm):
    class Meta:
        model = PotentialFellowship
        fields = ["status"]


class PotentialFellowshipEventForm(forms.ModelForm):
    class Meta:
        model = PotentialFellowshipEvent
        fields = ["event", "comments"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comments"].widget.attrs.update(
            {
                "placeholder": "NOTA BENE: careful, will be visible to all who have voting rights"
            }
        )


###############
# Nominations #
###############


class FellowshipNominationForm(forms.ModelForm):
    class Meta:
        model = FellowshipNomination
        fields = ["nominated_by", "college", "nominator_comments"]  # hidden  # visible

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        super().__init__(*args, **kwargs)
        self.fields["college"].queryset = College.objects.filter(
            acad_field=self.profile.acad_field
        )
        self.fields["college"].empty_label = None
        self.fields["nominator_comments"].label = False
        self.fields["nominator_comments"].widget.attrs["rows"] = 4
        self.fields["nominator_comments"].widget.attrs[
            "placeholder"
        ] = "Optional comments and/or recommendations"
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("profile_id", type="hidden"),
            Field("nominated_by", type="hidden"),
            Div(
                Div(Field("nominator_comments"), css_class="col-lg-8"),
                Div(
                    FloatingField("college"),
                    ButtonHolder(
                        Submit(
                            "submit", "Nominate", css_class="btn btn-success float-end"
                        )
                    ),
                    css_class="col-lg-4",
                ),
                css_class="row pt-1",
            ),
        )

    def clean(self):
        data = super().clean()
        failed_eligibility_criteria = check_profile_eligibility_for_fellowship(
            self.profile
        )
        if failed_eligibility_criteria:
            for critetion in failed_eligibility_criteria:
                self.add_error(None, criterion)
        if data["college"].acad_field != self.profile.acad_field:
            self.add_error(
                "college", "Mismatch between college.acad_field and profile.acad_field."
            )
        return data

    def save(self):
        nomination = super().save(commit=False)
        nomination.profile = self.profile
        nomination.save()
        return nomination


class FellowshipNominationSearchForm(forms.Form):
    """Filter a FellowshipNomination queryset using basic search fields."""

    college = forms.ModelChoiceField(queryset=College.objects.all(), required=False)
    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.all(),
        label="Specialty",
        required=False,
    )
    name = forms.CharField(max_length=128, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                FloatingField("category"),
                css_class="row",
            ),
            Div(
                Div(FloatingField("college"), css_class="col-lg-6"),
                Div(FloatingField("specialty"), css_class="col-lg-6"),
                css_class="row",
            ),
            Div(
                Div(FloatingField("name", autocomplete="off"), css_class="col-lg-6"),
                css_class="row",
            ),
        )

    def search_results(self):
        if self.cleaned_data.get("name"):
            nominations = FellowshipNomination.objects.filter(
                Q(profile__last_name__icontains=self.cleaned_data.get("name"))
                | Q(profile__first_name__icontains=self.cleaned_data.get("name"))
            )
        else:
            nominations = FellowshipNomination.objects.all()
        if self.cleaned_data.get("college"):
            nominations = nominations.filter(college=self.cleaned_data.get("college"))
        if self.cleaned_data.get("specialty"):
            nominations = nominations.filter(
                profile__specialties__in=[
                    self.cleaned_data.get("specialty"),
                ]
            )
        return nominations


class FellowshipNominationCommentForm(forms.ModelForm):
    class Meta:
        model = FellowshipNominationComment
        fields = [
            "nomination",
            "by",
            "text",
            "on",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["text"].label = False
        self.fields
        self.helper.layout = Layout(
            Field("nomination", type="hidden"),
            Field("by", type="hidden"),
            Field("on", type="hidden"),
            Div(
                Div(
                    Field(
                        "text",
                        placeholder="Add a comment (visible to EdAdmin and all Fellows)",
                        rows=2,
                    ),
                ),
                Div(ButtonHolder(Submit("submit", "Add comment"))),
                css_class="row",
            ),
        )


class FellowshipNominationDecisionForm(forms.ModelForm):
    class Meta:
        model = FellowshipNominationDecision
        fields: list[str] = [
            "voting_round",
            "outcome",
            "fixed_on",
            "comments",
        ]

    def __init__(self, *args, **kwargs):
        voting_round = kwargs.pop("voting_round", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("voting_round", type="hidden"),
            Field("fixed_on", type="hidden"),
            Div(
                Div(Field("comments"), css_class="col-8"),
                Div(
                    Field("outcome"),
                    ButtonHolder(Submit("submit", "Submit")),
                    css_class="col-4",
                ),
                css_class="row",
            ),
        )
        if voting_round:
            self.fields["voting_round"].initial = voting_round
            self.fields["outcome"].initial = voting_round.vote_outcome


class FellowshipInvitationResponseForm(forms.ModelForm):
    class Meta:
        model = FellowshipInvitation
        fields = [
            "nomination",
            "response",
            "postpone_start_to",
            "comments",
        ]
        widgets = {
            "postpone_start_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields
        self.helper.layout = Layout(
            Field("nomination", type="hidden"),
            Div(
                Div(Field("response"), css_class="col-lg-5"),
                Div(Field("postpone_start_to"), css_class="col-lg-5"),
                css_class="row",
            ),
            Div(
                Div(
                    Field(
                        "comments",
                        placeholder="Add a comment (visible to EdAdmin)",
                        rows=2,
                    ),
                    css_class="col-lg-10",
                ),
                Div(ButtonHolder(Submit("submit", "Submit")), css_class="col-lg-2"),
                css_class="row mt-0",
            ),
        )
