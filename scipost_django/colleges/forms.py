__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from typing import Any, Dict

from django import forms
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import F, Q, Count, OuterRef, Subquery
from django.db.models.functions import Coalesce

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit, HTML
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import timedelta

from ontology.models import Specialty
from ontology.models.academic_field import AcademicField
from proceedings.models import Proceedings
from profiles.models import Profile
from submissions.models import Submission
from submissions.models.assignment import EditorialAssignment
from submissions.models.qualification import Qualification
from submissions.models.recommendation import EICRecommendation
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

    invitation_response = forms.ChoiceField(
        choices=[("", "Any")] + FellowshipInvitation.RESPONSE_CHOICES,
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
    needs_edadmin_attention = forms.BooleanField(
        label="Needs EdAdmin attention",
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

        if is_edadmin(self.user):
            div_block_checkbox.append(
                Div(
                    Field("needs_edadmin_attention"),
                    css_class="col-auto col-lg-12 col-xl-auto",
                )
            )

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(FloatingField("nominee"), css_class="col-12 col-lg-6"),
                        Div(FloatingField("decision"), css_class="col-6 col-lg-3"),
                        Div(
                            FloatingField("invitation_response"),
                            css_class="col-6 col-lg-3",
                        ),
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
        if invitation_response := self.cleaned_data.get("invitation_response"):
            nominations = nominations.filter(
                invitation__response=invitation_response,
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

        # Render the queryset to evaluate properties
        nominations = list(nominations)

        if self.cleaned_data.get("needs_edadmin_attention"):
            nominations = [
                nomination for nomination in nominations if nomination.edadmin_notes
            ]

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
                        placeholder="Add a comment (visible to EdAdmin and Senior Fellows)",
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
        fields = ["type", "voting_opens", "voting_deadline"]

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
                Div(Field("type"), css_class="col-2"),
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
            "postponement_date",
            "comments",
        ]
        widgets = {
            "postponement_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("nomination", type="hidden"),
            Div(
                Div(
                    Div(
                        Div(Field("response"), css_class="col-12"),
                        Div(Field("postponement_date"), css_class="col-12"),
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
        invitation_postponed = self.cleaned_data["response"] in [
            FellowshipInvitation.RESPONSE_POSTPONED,
            FellowshipInvitation.RESPONSE_REINVITE_LATER,
        ]
        postponement_date = self.cleaned_data["postponement_date"]

        if postponement_date and (timezone.now().date() > postponement_date):
            self.add_error(
                "postponement_date",
                "You cannot set a postponed start date in the past.",
            )

        if (
            invitation_accepted
            and (postponement_date is not None)
            and (postponement_date != timezone.now().date())
        ):
            self.add_error(
                "postponement_date",
                "If the invitation is accepted for immediate start, you cannot postpone its start date.",
            )

        if invitation_postponed and not postponement_date:
            self.add_error(
                "postponement_date",
                "If the invitation is postponed, you must set a postponement date in the future.",
            )


class FellowshipsMonitorSearchForm(forms.Form):
    form_id = "fellowships-monitor-search-form"
    all_fellowships = Fellowship.objects.all()
    fellowships_colleges = all_fellowships.values_list("college", flat=True).distinct()
    fellowships_acad_fields = all_fellowships.values("college__acad_field")

    fellow = forms.CharField(max_length=100, required=False, label="Fellow")

    college = forms.MultipleChoiceField(
        choices=College.objects.filter(id__in=fellowships_colleges)
        .order_by("name")
        .values_list("id", "name"),
        required=False,
    )

    # Specialty multiple-choice grouped by the academic field that contains it.
    acad_fields = AcademicField.objects.filter(
        colleges__in=fellowships_acad_fields
    ).values_list("name", "id")
    specialty_grouped_choices = [
        (
            field_name,
            tuple(
                Specialty.objects.filter(acad_field=field_id).values_list("id", "name")
            ),
        )
        for (field_name, field_id) in acad_fields
    ]
    specialties = forms.MultipleChoiceField(
        choices=specialty_grouped_choices,
        label="Specialties",
        required=False,
    )

    date_from = forms.DateField(
        label="From date",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    date_to = forms.DateField(
        label="To date",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    has_regular = forms.BooleanField(
        label="Regular",
        required=False,
        initial=True,
    )
    has_senior = forms.BooleanField(
        label="Senior",
        required=False,
        initial=True,
    )
    has_guest = forms.BooleanField(
        label="Guest",
        required=False,
        initial=True,
    )
    show_expired = forms.BooleanField(
        label="Expired",
        required=False,
        initial=False,
    )

    orderby = forms.ChoiceField(
        label="Order by",
        choices=[
            ("nr_in_pool", "# in pool"),
            ("nr_appraised", "# appraised"),
            ("nr_assignments_completed", "# completed"),
            ("start_date", "Start date"),
            ("until_date", "End date"),
        ],
        required=False,
    )
    ordering = forms.ChoiceField(
        label="Ordering",
        choices=[
            ("-", "Descending"),
            ("+", "Ascending"),
        ],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.session_key = kwargs.pop("session_key", None)
        super().__init__(*args, **kwargs)

        # Set the initial values of the form fields from the session data
        if self.session_key:
            session = SessionStore(session_key=self.session_key)

            for field_key in self.fields:
                session_key = (
                    f"{self.form_id}_{field_key}"
                    if hasattr(self, "form_id")
                    else field_key
                )

                if session_value := session.get(session_key):
                    self.fields[field_key].initial = session_value

        self.helper = FormHelper()

        div_block_ordering = Div(
            Div(Field("orderby"), css_class="col-6"),
            Div(Field("ordering"), css_class="col-6"),
            css_class="row mb-0",
        )
        div_block_dates = Div(
            Div(Field("date_from"), css_class="col-6"),
            Div(Field("date_to"), css_class="col-6"),
            css_class="row mb-0",
        )
        div_block_fellow_types = Div(
            Div(Field("has_regular"), css_class="col-auto"),
            Div(Field("has_senior"), css_class="col-auto"),
            Div(Field("has_guest"), css_class="col-auto"),
            Div(Field("show_expired"), css_class="col-auto"),
            css_class="row mb-0",
        )

        # Date ranges until today
        today = date.today()
        time_ranges = [
            ("Last month", today - timedelta(days=30), today),
            ("Last year", today - timedelta(days=365), today),
            ("Last 2 years", today - timedelta(days=2 * 365), today),
        ]

        div_block_date_buttons = Div(
            Div(
                *[
                    HTML(
                        f'<button class="btn btn-outline-secondary" '
                        f"""hx-get={reverse("colleges:fellowships_monitor:_hx_search_form", kwargs={"filter_set":f"from_{from_date}_to_{to_date}"})} """
                        f'hx-target="#fellowships-monitor-search-form-container"'
                        f">{date_range_name}</button>"
                    )
                    for (date_range_name, from_date, to_date) in time_ranges
                ],
                css_class="d-grid gap-1 my-3",
            ),
            css_class="row mb-0",
        )

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(Field("fellow"), css_class="col-12 mb-2"),
                        Div(div_block_fellow_types, css_class="col-12"),
                        Div(Field("college", size=8), css_class="col-12"),
                        css_class="row mb-0 d-flex flex-column justify-content-between h-100",
                    ),
                    css_class="col",
                ),
                Div(
                    Field("specialties", size=13),
                    css_class="col-12 col-sm-6 col-md-4 col-lg-5 col-xl-6",
                ),
                Div(
                    Div(
                        Div(div_block_dates, css_class="col-12"),
                        Div(div_block_date_buttons, css_class="col-12"),
                        Div(div_block_ordering, css_class="col-12"),
                        css_class="row mb-0 d-flex flex-column justify-content-between h-100",
                    ),
                    css_class="col-12 col-md",
                ),
                css_class="row mb-0",
            ),
        )

    def save_fields_to_session(self):
        # Save the form data to the session
        if self.session_key is not None:
            session = SessionStore(session_key=self.session_key)

            for field_key in self.cleaned_data:
                session_key = (
                    f"{self.form_id}_{field_key}"
                    if hasattr(self, "form_id")
                    else field_key
                )

                if field_value := self.cleaned_data.get(field_key):
                    if isinstance(field_value, date):
                        field_value = field_value.strftime("%Y-%m-%d")

                session[session_key] = field_value

            session.save()

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
        self.save_fields_to_session()

        fellowships = Fellowship.objects.all().distinct()

        if fellow := self.cleaned_data.get("fellow"):
            fellowships = fellowships.filter(
                Q(contributor__profile__first_name__unaccent__icontains=fellow)
                | Q(contributor__profile__last_name__unaccent__icontains=fellow)
            )
        if college := self.cleaned_data.get("college"):
            fellowships = fellowships.filter(college__id__in=college)
        if specialties := self.cleaned_data.get("specialties"):
            fellowships = fellowships.filter(
                contributor__profile__specialties__in=specialties
            )

        date_from = self.cleaned_data.get("date_from")
        date_to = self.cleaned_data.get("date_to")

        def filter_submissions_in_pool(qs, prefix=""):
            """
            Filter a Submission queryset to only items in the pool between some dates.
            """
            if not date_from and not date_to:
                return qs
            else:
                date_filter = Q()

            # Should not have left the pool before the "from" start date or not left at all
            if date_from:
                date_filter = Q(**{prefix + "eic_first_assigned_date__isnull": True})
                date_filter |= Q(**{prefix + "eic_first_assigned_date__gte": date_from})

            # Should have been added to the pool before the "to" final date
            # Only dates in the past can change the query result
            if date_to and date_to < date.today():
                date_filter &= Q(**{prefix + "checks_cleared_date__lte": date_to})

            return qs.filter(date_filter)

        def count_q(qs, key="pk"):
            """Count the number of items in a queryset, or return 0 if the queryset is empty."""
            return Coalesce(
                Subquery(qs.values(key).annotate(count=Count(key)).values("count")),
                0,
            )

        fellowships = fellowships.annotate(
            nr_in_pool=count_q(
                filter_submissions_in_pool(
                    Submission.objects.filter(fellows__exact=OuterRef("id")),
                ),
                key="fellows",
            ),
            nr_appraised=count_q(
                filter_submissions_in_pool(
                    Qualification.objects.filter(fellow=OuterRef("id")),
                    prefix="submission__",
                ),
                key="fellow",
            ),
            nr_qualified_for=count_q(
                filter_submissions_in_pool(
                    Qualification.objects.filter(
                        fellow=OuterRef("id"),
                        expertise_level__in=[
                            Qualification.EXPERT,
                            Qualification.VERY_KNOWLEDGEABLE,
                            Qualification.KNOWLEDGEABLE,
                            Qualification.MARGINALLY_QUALIFIED,
                        ],
                    ),
                    prefix="submission__",
                ),
                key="fellow",
            ),
            nr_assignments_completed=count_q(
                filter_submissions_in_pool(
                    EditorialAssignment.objects.filter(
                        to=OuterRef("contributor"),
                        status=EditorialAssignment.STATUS_COMPLETED,
                    ),
                    prefix="submission__",
                ),
                key="to",
            ),
            nr_assignments_ongoing=count_q(
                filter_submissions_in_pool(
                    EditorialAssignment.objects.filter(
                        to=OuterRef("contributor"),
                        status=EditorialAssignment.STATUS_ACCEPTED,
                    ),
                    prefix="submission__",
                ),
                key="to",
            ),
            nr_recommendations_eligible=count_q(
                filter_submissions_in_pool(
                    EICRecommendation.objects.filter(
                        eligible_to_vote__exact=OuterRef("contributor")
                    ),
                    prefix="submission__",
                ),
                key="eligible_to_vote",
            ),
            nr_recommendations_voted_for=count_q(
                filter_submissions_in_pool(
                    EICRecommendation.objects.filter(
                        voted_for__exact=OuterRef("contributor"),
                    ),
                    prefix="submission__",
                ),
                key="voted_for",
            ),
            nr_recommendations_voted_against=count_q(
                filter_submissions_in_pool(
                    EICRecommendation.objects.filter(
                        voted_against__exact=OuterRef("contributor"),
                    ),
                    prefix="submission__",
                ),
                key="voted_against",
            ),
            nr_recommendations_voted_abstain=count_q(
                filter_submissions_in_pool(
                    EICRecommendation.objects.filter(
                        voted_abstain__exact=OuterRef("contributor"),
                    ),
                    prefix="submission__",
                ),
                key="voted_abstain",
            ),
        ).annotate(
            nr_recommendations_voted=F("nr_recommendations_voted_for")
            + F("nr_recommendations_voted_against")
            + F("nr_recommendations_voted_abstain")
        )

        if not self.cleaned_data.get("has_regular"):
            fellowships = fellowships.exclude(status=Fellowship.STATUS_REGULAR)
        if not self.cleaned_data.get("has_senior"):
            fellowships = fellowships.exclude(status=Fellowship.STATUS_SENIOR)
        if not self.cleaned_data.get("has_guest"):
            fellowships = fellowships.exclude(status=Fellowship.STATUS_GUEST)
        if not self.cleaned_data.get("show_expired"):
            fellowships = fellowships.filter(until_date__gte=timezone.now())

        # Ordering of nominations
        # Only order if both fields are set
        if (orderby_value := self.cleaned_data.get("orderby")) and (
            ordering_value := self.cleaned_data.get("ordering")
        ):
            # Remove the + from the ordering value, causes a Django error
            ordering_value = ordering_value.replace("+", "")

            # Ordering string is built by the ordering (+/-), and the field name
            # from the orderby field split by "," and joined together
            fellowships = fellowships.order_by(
                *[
                    ordering_value + order_part
                    for order_part in orderby_value.split(",")
                ]
            )

        return fellowships
