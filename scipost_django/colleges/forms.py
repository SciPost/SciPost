__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from typing import Any, Dict

from django import forms
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import Q, Max, OuterRef, Subquery

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit, HTML
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import timedelta

from ontology.models import Specialty
from proceedings.models import Proceedings
from profiles.models import Profile
from submissions.models import Submission
from scipost.forms import RequestFormMixin
from scipost.models import Contributor

from colleges.permissions import is_edadmin

from .models import (
    College,
    Fellowship,
    PotentialFellowship,
    PotentialFellowshipEvent,
    FellowshipNomination,
    FellowshipNominationComment,
    FellowshipNominationDecision,
    FellowshipNominationVotingRound,
    FellowshipNominationEvent,
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
        if q := self.cleaned_data["q"]:
            fellowships = Fellowship.objects.filter(
                Q(contributor__profile__last_name__unaccent__icontains=q)
                | Q(contributor__profile__first_name__unaccent__icontains=q)
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

    specialties = forms.MultipleChoiceField(
        choices=[],
        label="Specialties",
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        super().__init__(*args, **kwargs)
        self.fields["college"].queryset = College.objects.filter(
            acad_field=self.profile.acad_field,
            # id__in=Fellowship.objects.active()
            # .filter(contributor=self.fields["nominated_by"].initial)
            # .values_list("college", flat=True),
        )
        self.fields["college"].empty_label = None
        self.fields["nominator_comments"].label = False
        self.fields["nominator_comments"].widget = forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Please provide a short motivation for the nomination, "
                "as well as a personal website or external profile page to help us identify the nominee.",
            }
        )
        self.fields["nominator_comments"].required = True

        self.fields["specialties"].choices = [
            (s.pk, s.name)
            for s in Specialty.objects.filter(acad_field=self.profile.acad_field)
        ]
        self.fields["specialties"].initial = list(
            self.profile.specialties.all().values_list("pk", flat=True)
        )

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
                Div(
                    Field(
                        "specialties",
                        css_class="border border-secondary p-2 d-flex flex-wrap gap-3",
                    ),
                    css_class="col-12",
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
            for criterion in failed_eligibility_criteria:
                self.add_error(None, criterion)
        if data["college"].acad_field != self.profile.acad_field:
            self.add_error(
                "college", "Mismatch between college.acad_field and profile.acad_field."
            )
        if (not is_edadmin(data["nominated_by"].user)) and (
            data["college"].id
            not in Fellowship.objects.active()
            .filter(contributor=data["nominated_by"])
            .values_list("college", flat=True)
        ):
            self.add_error(
                "college",
                "You do not have an active Fellowship in the selected College.",
            )

        profile_specialties_of_field = self.profile.specialties.filter(
            acad_field=data["college"].acad_field
        )
        if profile_specialties_of_field.count() == 0 and len(data["specialties"]) == 0:
            self.add_error(
                None,
                "You must denote at least one specialty for the nominee in their nominated college.",
            )
        return data

    def save(self):
        nomination = super().save(commit=False)
        nomination.profile = self.profile
        # add specialties to profile
        nomination.profile.specialties.add(*self.cleaned_data["specialties"])
        nomination.save()
        return nomination


# class FellowshipNominationSearchForm(forms.Form):
#     """Filter a FellowshipNomination queryset using basic search fields."""

#     college = forms.ModelChoiceField(queryset=College.objects.all(), required=False)
#     specialty = forms.ModelChoiceField(
#         queryset=Specialty.objects.all(),
#         label="Specialty",
#         required=False,
#     )
#     name = forms.CharField(max_length=128, required=False)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.layout = Layout(
#             Div(
#                 FloatingField("category"),
#                 css_class="row",
#             ),
#             Div(
#                 Div(FloatingField("college"), css_class="col-lg-6"),
#                 Div(FloatingField("specialty"), css_class="col-lg-6"),
#                 css_class="row",
#             ),
#             Div(
#                 Div(FloatingField("name", autocomplete="off"), css_class="col-lg-6"),
#                 css_class="row",
#             ),
#         )

#     def search_results(self):
#         if self.cleaned_data.get("name"):
#             nominations = FellowshipNomination.objects.filter(
#                 Q(profile__last_name__icontains=self.cleaned_data.get("name"))
#                 | Q(profile__first_name__icontains=self.cleaned_data.get("name"))
#             )
#         else:
#             nominations = FellowshipNomination.objects.all()
#         if self.cleaned_data.get("college"):
#             nominations = nominations.filter(college=self.cleaned_data.get("college"))
#         if self.cleaned_data.get("specialty"):
#             nominations = nominations.filter(
#                 profile__specialties__in=[
#                     self.cleaned_data.get("specialty"),
#                 ]
#             )
#         return nominations


class FellowshipNominationSearchForm(forms.Form):
    all_nominations = FellowshipNomination.objects.all()
    nomination_colleges = all_nominations.values_list("college", flat=True).distinct()

    nominee = forms.CharField(max_length=100, required=False, label="Nominee")

    college = forms.MultipleChoiceField(
        choices=College.objects.filter(id__in=nomination_colleges)
        .order_by("name")
        .values_list("id", "name"),
        required=False,
    )

    decision = forms.ChoiceField(
        choices=[("", "Any"), ("pending", "Pending")]
        + FellowshipNominationDecision.OUTCOME_CHOICES,
        required=False,
    )

    can_vote = forms.BooleanField(
        label="I can vote",
        required=False,
        initial=True,
    )
    voting_open = forms.BooleanField(
        label="Voting open now",
        required=False,
        initial=True,
    )
    has_rounds = forms.BooleanField(
        label="Has voting rounds",
        required=False,
        initial=True,
    )
    needs_specialties = forms.BooleanField(
        label="Needs specialties",
        required=False,
        initial=False,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("latest_round_deadline", "Deadline"),
            ("latest_round_open", "Voting start"),
            ("latest_round_decision_outcome", "Decision"),
            ("profile__last_name", "Nominee"),
            ("nominated_on", "Nominated date"),
        ),
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            # FIXME: Emperically, the ordering appers to be reversed for dates?
            ("-", "Ascending"),
            ("+", "Descending"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.session_key = kwargs.pop("session_key", None)
        super().__init__(*args, **kwargs)

        # Set the initial values of the form fields from the session data
        if self.session_key:
            session = SessionStore(session_key=self.session_key)

            for field in self.fields:
                if field in session:
                    self.fields[field].initial = session[field]

        self.helper = FormHelper()

        div_block_ordering = Div(
            Div(FloatingField("orderby"), css_class="col-6 col-md-12 col-xl-6"),
            Div(FloatingField("ordering"), css_class="col-6 col-md-12 col-xl-6"),
            css_class="row mb-0",
        )
        div_block_checkbox = Div(
            Div(Field("can_vote"), css_class="col-auto col-lg-12 col-xl-auto"),
            Div(Field("voting_open"), css_class="col-auto col-lg-12 col-xl-auto"),
            Div(Field("has_rounds"), css_class="col-auto col-lg-12 col-xl-auto"),
            Div(Field("needs_specialties"), css_class="col-auto col-lg-12 col-xl-auto"),
            css_class="row mb-0",
        )

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(FloatingField("nominee"), css_class="col-8"),
                        Div(FloatingField("decision"), css_class="col-4"),
                        Div(div_block_ordering, css_class="col-12 col-md-6 col-xl-12"),
                        Div(div_block_checkbox, css_class="col-12 col-md-6 col-xl-12"),
                        css_class="row mb-0",
                    ),
                    css_class="col",
                ),
                Div(
                    Field("college", size=6),
                    css_class="col-12 col-md-6 col-lg-4",
                ),
                css_class="row mb-0",
            ),
        )

    def apply_filter_set(self, filters: Dict, none_on_empty: bool = False):
        # Apply the filter set to the form
        for key in self.fields:
            if key in filters:
                self.fields[key].initial = filters[key]
            elif none_on_empty:
                if isinstance(self.fields[key], forms.MultipleChoiceField):
                    self.fields[key].initial = []
                else:
                    self.fields[key].initial = None

    def search_results(self):
        # Save the form data to the session
        if self.session_key is not None:
            session = SessionStore(session_key=self.session_key)

            for key in self.cleaned_data:
                session[key] = self.cleaned_data.get(key)

            session.save()

        def latest_round_subquery(key):
            return Subquery(
                FellowshipNominationVotingRound.objects.filter(
                    nomination=OuterRef("pk")
                )
                .order_by("-voting_deadline")
                .values(key)[:1]
            )

        nominations = (
            FellowshipNomination.objects.all()
            .annotate(
                latest_round_deadline=latest_round_subquery("voting_deadline"),
                latest_round_open=latest_round_subquery("voting_opens"),
                latest_round_decision_outcome=latest_round_subquery(
                    "decision__outcome"
                ),
            )
            .distinct()
        )

        if self.cleaned_data.get("can_vote"):
            # Restrict rounds to those the user can vote on
            nominations = nominations.with_user_votable_rounds(self.user).distinct()

        if nominee := self.cleaned_data.get("nominee"):
            nominations = nominations.filter(
                Q(profile__first_name__unaccent__icontains=nominee)
                | Q(profile__last_name__unaccent__icontains=nominee)
            )
        if college := self.cleaned_data.get("college"):
            nominations = nominations.filter(college__id__in=college)
        if decision := self.cleaned_data.get("decision"):
            if decision == "pending":
                nominations = nominations.filter(
                    voting_rounds__decision__isnull=True,
                )
            else:
                nominations = nominations.filter(
                    voting_rounds__decision__outcome=decision,
                )
        if self.cleaned_data.get("voting_open"):
            nominations = nominations.filter(
                Q(voting_rounds__voting_opens__lte=timezone.now())
                & Q(voting_rounds__voting_deadline__gte=timezone.now())
            )
        if self.cleaned_data.get("has_rounds"):
            nominations = nominations.filter(voting_rounds__isnull=False)
        if self.cleaned_data.get("needs_specialties"):
            nominations = nominations.filter(profile__specialties__isnull=True)

        # Ordering of nominations
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            nominations = nominations.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
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
        fields = [
            "voting_round",
            "outcome",
            "fixed_on",
            "comments",
        ]

        widgets = {
            "comments": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        voting_round = kwargs.pop("voting_round", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("voting_round", type="hidden"),
            Field("fixed_on", type="hidden"),
            Div(
                Div(Field("comments"), css_class="col-12 col-lg-8"),
                Div(
                    Field("outcome"),
                    ButtonHolder(Submit("submit", "Submit")),
                    css_class="col-12 col-lg-4",
                ),
                css_class="row",
            ),
        )
        if voting_round:
            self.fields["voting_round"].initial = voting_round
            self.fields["outcome"].initial = voting_round.vote_outcome

        if nomination := getattr(self.instance, "nomination", None):
            if voting_outcome := nomination.latest_voting_round.outcome:
                self.fields["outcome"].initial = voting_outcome


#################
# Voting Rounds #
#################


class FellowshipNominationVotingRoundSearchForm(forms.Form):
    all_rounds = FellowshipNominationVotingRound.objects.all()

    nominee = forms.CharField(max_length=100, required=False, label="Nominee")

    college = forms.MultipleChoiceField(
        choices=College.objects.all().order_by("name").values_list("id", "name"),
        required=False,
    )

    decision = forms.ChoiceField(
        choices=[("", "Any"), ("pending", "Pending")]
        + FellowshipNominationDecision.OUTCOME_CHOICES,
        required=False,
    )

    can_vote = forms.BooleanField(
        label="I can vote",
        required=False,
        initial=True,
    )
    voting_open = forms.BooleanField(
        label="Voting open",
        required=False,
        initial=True,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=(
            ("voting_deadline", "Deadline"),
            ("voting_opens", "Voting start"),
            ("decision__outcome", "Decision"),
            ("nomination__profile__last_name", "Nominee"),
        ),
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=(
            # FIXME: Emperically, the ordering appers to be reversed for dates?
            ("-", "Ascending"),
            ("+", "Descending"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.session_key = kwargs.pop("session_key", None)
        super().__init__(*args, **kwargs)

        # Set the initial values of the form fields from the session data
        if self.session_key:
            session = SessionStore(session_key=self.session_key)

            for field in self.fields:
                if field in session:
                    self.fields[field].initial = session[field]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(FloatingField("nominee"), css_class="col-6 col-lg-6"),
                        Div(FloatingField("decision"), css_class="col-3 col-lg-4"),
                        Div(
                            Div(
                                Div(Field("can_vote"), css_class="col-12"),
                                Div(Field("voting_open"), css_class="col-12"),
                                css_class="row mb-0",
                            ),
                            css_class="col-3 col-lg-2",
                        ),
                        Div(FloatingField("orderby"), css_class="col-6"),
                        Div(FloatingField("ordering"), css_class="col-6"),
                        css_class="row mb-0",
                    ),
                    css_class="col",
                ),
                Div(
                    Field("college", size=5),
                    css_class="col-12 col-md-6 col-lg-4",
                ),
                css_class="row mb-0",
            ),
        )

    def apply_filter_set(self, filters: Dict, none_on_empty: bool = False):
        # Apply the filter set to the form
        for key in self.fields:
            if key in filters:
                self.fields[key].initial = filters[key]
            elif none_on_empty:
                if isinstance(self.fields[key], forms.MultipleChoiceField):
                    self.fields[key].initial = []
                else:
                    self.fields[key].initial = None

    def search_results(self):
        # Save the form data to the session
        if self.session_key is not None:
            session = SessionStore(session_key=self.session_key)

            for key in self.cleaned_data:
                session[key] = self.cleaned_data.get(key)

            session.save()

        rounds = FellowshipNominationVotingRound.objects.all()

        if self.cleaned_data.get("can_vote"):
            # or not self.user.has_perm("scipost.can_view_all_nomination_voting_rounds"):
            # Restrict rounds to those the user can vote on
            rounds = rounds.where_user_can_vote(self.user)

        if nominee := self.cleaned_data.get("nominee"):
            rounds = rounds.filter(
                Q(nomination__profile__first_name__icontains=nominee)
                | Q(nomination__profile__last_name__icontains=nominee)
            )
        if college := self.cleaned_data.get("college"):
            rounds = rounds.filter(nomination__college__id__in=college)
        if decision := self.cleaned_data.get("decision"):
            if decision == "pending":
                rounds = rounds.filter(decision__isnull=True)
            else:
                rounds = rounds.filter(decision__outcome=decision)
        if self.cleaned_data.get("voting_open"):
            rounds = rounds.filter(
                Q(voting_opens__lte=timezone.now())
                & Q(voting_deadline__gte=timezone.now())
            )

        # Ordering of voting rounds
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            rounds = rounds.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

        return rounds


from datetime import date


class FellowshipNominationVotingRoundStartForm(forms.ModelForm):
    class Meta:
        model = FellowshipNominationVotingRound
        fields = ["voting_opens", "voting_deadline"]

        widgets = {
            "voting_opens": forms.DateInput(attrs={"type": "date"}),
            "voting_deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = date.today()
        self.fields["voting_opens"].widget.attrs.update(
            {
                "min": today.strftime("%Y-%m-%d"),
                "value": today.strftime("%Y-%m-%d"),
            }
        )

        in_two_weeks = today + timedelta(days=14)
        self.fields["voting_deadline"].widget.attrs.update(
            {
                "min": today.strftime("%Y-%m-%d"),
                "value": in_two_weeks.strftime("%Y-%m-%d"),
            }
        )

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-target": f"#nomination-{self.instance.nomination.id}-round-tab-holder",
            "hx-swap": "outerHTML",
            "hx-post": reverse(
                "colleges:_hx_nomination_voting_rounds_tab",
                kwargs={
                    "nomination_id": self.instance.nomination.id,
                    "round_id": self.instance.id,
                },
            ),
        }
        self.helper.layout = Layout(
            Div(
                Div(Field("voting_opens"), css_class="col"),
                Div(Field("voting_deadline"), css_class="col"),
                Div(
                    ButtonHolder(Submit("submit", "Start")),
                    css_class="col-auto align-self-end mb-3",
                ),
                Div(
                    HTML(
                        "Tip: Set both dates to today and remove all fellows to take decision immediately."
                    ),
                    css_class="col-12 text-muted small",
                ),
                css_class="row mb-0",
            )
        )

    def clean(self):
        open_date = self.cleaned_data.get("voting_opens", None)
        deadline_date = self.cleaned_data.get("voting_deadline", None)

        if open_date is None or deadline_date is None:
            self.add_error(
                None,
                "Both the voting opens and voting deadline must be set.",
            )

        # Check that the voting deadline is after the voting opens
        if deadline_date <= open_date:
            self.add_error(
                "voting_deadline",
                "The voting deadline must be after the voting opens.",
            )

        # Check that the voting opens after today
        if open_date.date() < date.today():
            self.add_error(
                "voting_opens", "The voting opening date may not be in the past."
            )

        if self.instance.eligible_to_vote.count() == 0:
            # If both dates are set to today, then it is implied that
            # the voting round should never be opened and
            # the decision should be made by the foundation
            if open_date.date() == deadline_date.date() == date.today():
                yesterday = date.today() - timedelta(days=1)
                self.instance.voting_opens = yesterday
                self.instance.voting_deadline = yesterday
                self.instance.save()

            # If the dates are propertly set, just error out
            else:
                self.add_error(
                    None,
                    "There must be at least one eligible voter to start the round. "
                    "Please add voters to the round before setting the dates.",
                )


class FellowshipNominationVetoForm(forms.Form):
    edadmin_comments = forms.CharField(
        label="Comments for editorial administration",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=True,
    )

    fellow_comments = forms.CharField(
        label="Comments for voting Fellows",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.fellow = kwargs.pop("fellow", None)
        self.nomination = kwargs.pop("nomination", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-post": reverse(
                "colleges:_hx_nomination_veto",
                kwargs={"nomination_id": self.nomination.id},
            ),
            "hx-target": "closest .veto-btn-container",
            "hx-swap": "outerHTML",
        }

        self.helper.layout = Layout(
            Div(
                Div(Field("edadmin_comments"), css_class="col"),
                Div(Field("fellow_comments"), css_class="col"),
                Div(
                    ButtonHolder(Submit("submit", "Veto", css_class="btn btn-dark")),
                    css_class="col-auto d-flex align-items-end",
                ),
                css_class="row mb-0",
            ),
        )

    def save(self):
        self.nomination.vetoes.add(self.fellow)
        self.nomination.save()

        # Fellow's comments are added as a regular comment
        FellowshipNominationComment.objects.create(
            nomination=self.nomination,
            by=self.fellow.contributor,
            text=self.cleaned_data["fellow_comments"],
        )

        # EdAdmin's comments are added as an event
        FellowshipNominationEvent.objects.create(
            nomination=self.nomination,
            by=self.fellow.contributor,
            description=f"Vetoed with justification: {self.cleaned_data['edadmin_comments']}",
        )


###############
# Invitations #
###############
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
                Div(
                    Div(
                        Div(Field("response"), css_class="col-12"),
                        Div(Field("postpone_start_to"), css_class="col-12"),
                        css_class="row mb-0",
                    ),
                    css_class="col-12 col-md-5",
                ),
                Div(
                    Field(
                        "comments",
                        placeholder="Add a comment (visible to EdAdmin)",
                        rows=4,
                    ),
                    css_class="col-12 col-md-7",
                ),
                Div(ButtonHolder(Submit("submit", "Update")), css_class="col-auto"),
                css_class="row mb-0",
            ),
        )

    def clean(self):
        invitation_accepted = self.cleaned_data["response"] == (
            FellowshipInvitation.RESPONSE_ACCEPTED
        )
        invitation_postponed = self.cleaned_data["response"] == (
            FellowshipInvitation.RESPONSE_POSTPONED
        )
        postponed_date = self.cleaned_data["postpone_start_to"]

        if postponed_date and (timezone.now().date() > postponed_date):
            self.add_error(
                "postpone_start_to",
                "You cannot set a postponed start date in the past.",
            )

        if (
            invitation_accepted
            and (postponed_date is not None)
            and (postponed_date != timezone.now().date())
        ):
            self.add_error(
                "postpone_start_to",
                "If the invitation is accepted for immediate start, you cannot postpone its start date.",
            )

        if invitation_postponed and not postponed_date:
            self.add_error(
                "postpone_start_to",
                "If the invitation is postponed, you must set a start date in the future.",
            )
