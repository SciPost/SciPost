__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from abc import ABC
from typing import TYPE_CHECKING, Any

from django import forms
from django.db import models
from django.db.models.functions import Coalesce, Concat, ExtractDay
from django.utils.timezone import datetime
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from colleges.models import Fellowship
from finances.models import PubFrac, Subsidy
from journals.models import Journal, Publication, PublicationAuthorsTable
from ontology.models.specialty import Specialty
from organizations.models import Organization
from profiles.models import Affiliation, Profile
from series.models import Collection
from submissions.models import Report, Submission
from submissions.models.decision import EditorialDecision
from submissions.models.recommendation import EICRecommendation
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.submission import SubmissionAuthorProfile, SubmissionEvent

from .options import BaseOptions

from crispy_forms.layout import Layout, Div, Field

OptionDict = dict[str, Any]

if TYPE_CHECKING:
    from .plotkind import PlotKind


class ModelFieldPlotter(ABC):
    model: type
    name: str | None = None

    class Options(BaseOptions):
        prefix = "model_field_plotter_"
        model_fields = (("id", ("int", "ID")),)

    def __init__(self, options: OptionDict = {}):
        self.options = self.Options.parse_prefixed_options(options)

    @classmethod
    def from_name(cls, name: str, *args, **kwargs):
        from graphs.graphs import ALL_PLOTTERS

        if cls_name := ALL_PLOTTERS.get(name, None):
            return cls_name(*args, **kwargs)

    @classmethod
    def get_name(cls) -> str:
        return cls.name or cls.model.__name__

    def get_model_field_display(self, key: str | None) -> str | None:
        if (
            key is not None
            and (options := getattr(self, "Options", None))
            and (model_fields := getattr(options, "model_fields", None))
        ):
            for field, (_, value_display) in model_fields:
                if field == key:
                    return value_display

    def get_model_field_type(self, key: str | None) -> str | None:
        if (
            key is not None
            and (options := getattr(self, "Options", None))
            and (model_fields := getattr(options, "model_fields", None))
        ):
            for field, (field_type, _) in model_fields:
                if field == key:
                    return field_type

    def __str__(self):
        return self.get_name()

    def get_queryset(self) -> models.QuerySet[Any]:
        qs = self.model.objects.all()
        return qs

    def get_available_plot_kinds(self) -> list[str]:
        """Returns the plot kinds that can be used with this model field."""
        try:
            model_fields_types = [
                field_type for _, (field_type, _) in self.Options.model_fields
            ]
        except AttributeError:
            return []

        plot_kinds: list[str] = []
        if "date" in model_fields_types or "datetime" in model_fields_types:
            plot_kinds.append("timeline")
        if "country" in model_fields_types:
            plot_kinds.append("map")
        if "int" in model_fields_types or "float" in model_fields_types:
            plot_kinds.append("bar")

        return plot_kinds

    def plot(self, kind: "PlotKind", options: OptionDict) -> Figure:
        """
        Create a plot of the model field according to the given kind.
        Further modify the plot according to the given options.
        """
        from graphs.graphs import ALL_MPL_THEMES

        plt.style.use(
            [
                ALL_MPL_THEMES.get("_base", ""),
                ALL_MPL_THEMES.get(options.get("theme", None), "light"),
            ]
        )
        fig = kind.plot(
            fig_kwargs={
                "figsize": (
                    options.get("fig_width", 6) or 6,
                    options.get("fig_height", 4) or 4,
                )
            }
        )

        main_ax, *_ = fig.get_axes()

        if title := options.get("title", None):
            main_ax.set_title(title)

        if x_label := options.get("x_label", main_ax.get_xlabel()):
            main_ax.set_xlabel(x_label)

        if y_label := options.get("y_label", main_ax.get_ylabel()):
            main_ax.set_ylabel(y_label)

        return fig

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Div()


class PublicationPlotter(ModelFieldPlotter):
    model = Publication
    name = "Publication"

    class Options(ModelFieldPlotter.Options):
        journals = forms.ModelMultipleChoiceField(
            queryset=Journal.objects.all().active(), required=False
        )
        collections = forms.ModelMultipleChoiceField(
            queryset=Collection.objects.all(), required=False
        )
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("submission_date", ("date", "Submission date")),
            ("submission_date__year", ("int", "Year submitted")),
            ("publication_date", ("date", "Publication date")),
            ("publication_date__year", ("int", "Year published")),
            ("acceptance_date", ("date", "Acceptance date")),
            ("acceptance_date__year", ("int", "Year accepted")),
            ("acceptance_duration", ("int", "Acceptance duration (days)")),
            ("publication_duration", ("int", "Publication duration (days)")),
            ("production_duration", ("int", "Production duration (days)")),
            ("nr_versions", ("int", "Number of versions")),
            ("acad_field__name", ("str", "Academic field")),
            ("specialties__name", ("str", "Specialties")),
            ("number_of_citations", ("int", "Number of citations")),
        )

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(pubtype="article")

        qs = qs.annotate(
            acceptance_duration=ExtractDay(
                models.F("acceptance_date") - models.F("submission_date")
            ),
            publication_duration=ExtractDay(
                models.F("publication_date") - models.F("submission_date")
            ),
            production_duration=ExtractDay(
                models.F("publication_date") - models.F("acceptance_date")
            ),
            nr_versions=models.Subquery(
                Submission.objects.filter(
                    thread_hash=models.OuterRef("accepted_submission__thread_hash")
                )
                .values("thread_hash")
                .annotate(nr_versions=models.Count("thread_hash"))
                .values("nr_versions")
            ),
        )

        if journals := self.options.get("journals", None):
            qs = qs.for_journals(journals)
        if collections := self.options.get("collections", None):
            qs = qs.filter(collections__in=collections)

        return qs


class SubmissionsPlotter(ModelFieldPlotter):
    model = Submission

    class Options(ModelFieldPlotter.Options):
        per_thread = forms.ChoiceField(
            required=False,
            label="Keep Submissions of thread",
            choices=[("all", "All"), ("first", "First"), ("last", "Last")],
        )
        submission_date_start = forms.DateField(
            required=False,
            label="Submitted after",
            widget=forms.DateInput(attrs={"type": "date"}),
        )
        submission_date_end = forms.DateField(
            required=False,
            label="Submitted before",
            widget=forms.DateInput(attrs={"type": "date"}),
        )
        submitted_to = forms.ModelMultipleChoiceField(
            required=False,
            label="Target journal",
            queryset=Journal.objects.all().active(),
        )
        specialties = forms.ModelMultipleChoiceField(
            required=False,
            label="Specialties",
            queryset=Specialty.objects.filter(journals__isnull=False).distinct(),
        )
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("submission_date", ("date", "Submission date")),
            ("submission_date__year", ("int", "Year submitted")),
            ("status", ("str", "Status")),
            ("topics__name", ("str", "Topics")),
            ("acad_field__name", ("str", "Academic field")),
            ("specialties__name", ("str", "Specialties")),
            ("submitted_to__name", ("str", "Target journal")),
            ("proceedings__event_suffix", ("str", "Proceedings")),
            ("nr_invitations", ("int", "Number of invitations")),
            ("nr_reports", ("int", "Number of reports")),
            ("report_turnover", ("float", "Report turnover")),
            ("preassignment_completed_date", ("date", "Preassignment completed date")),
            ("editor_first_assigned_date", ("date", "Editor first assigned date")),
            ("first_referee_invited_date", ("date", "First referee invited date")),
            ("withdrawal_date", ("date", "Withdrawal date")),
            (
                "preassignment_completed_duration",
                ("int", "Preassignment duration (days)"),
            ),
            ("eic_assignment_duration", ("int", "EIC assignment duration (days)")),
            (
                "first_referee_invitation_submission_duration",
                ("int", "Submission to first ref. invitation sent (days)"),
            ),
            (
                "first_referee_invitation_assignment_duration",
                ("int", "EIC assignment to first ref. invitation sent (days)"),
            ),
        )

    def get_queryset(self):
        qs = super().get_queryset()

        if start := self.options.get("submission_date_start", None):
            qs = qs.filter(submission_date__gte=start)
        if end := self.options.get("submission_date_end", None):
            qs = qs.filter(submission_date__lte=end)

        if journals := self.options.get("submitted_to", None):
            qs = qs.filter(submitted_to__in=journals)

        if specialties := self.options.get("specialties", None):
            qs = qs.filter(specialties__in=specialties)

        qs = qs.annotate(
            preassignment_completed_date=models.Subquery(
                SubmissionEvent.objects.filter(
                    submission=models.OuterRef("id"),
                    text__regex=r"Submission (passed|failed) pre(-screening|assignment)\.",
                ).values("created")[:1]
            ),
            editor_first_assigned_date=models.Subquery(
                SubmissionEvent.objects.filter(
                    submission=models.OuterRef("id"),
                    text="The Editor-in-charge has been assigned.",
                ).values("created")[:1]
            ),
            first_referee_invited_date=models.Subquery(
                RefereeInvitation.objects.filter(
                    submission=models.OuterRef("id"),
                )
                .order_by("date_invited")[:1]
                .values("date_invited")
            ),
            withdrawal_date=models.Subquery(
                SubmissionEvent.objects.filter(
                    submission=models.OuterRef("id"),
                    text__contains="withdrawn by the authors",
                ).values("created")[:1]
            ),
            nr_invitations=Coalesce(
                models.Subquery(
                    RefereeInvitation.objects.filter(submission=models.OuterRef("id"))
                    .values("submission")
                    .annotate(nr=models.Count("submission"))
                    .values("nr")
                ),
                models.Value(0),
            ),
            nr_reports=Coalesce(
                models.Subquery(
                    Report.objects.filter(submission=models.OuterRef("id"))
                    .values("submission")
                    .annotate(nr=models.Count("submission"))
                    .values("nr")
                ),
                models.Value(0),
            ),
            report_turnover=models.Case(
                models.When(
                    nr_invitations=0,
                    then=models.Value(0),
                ),
                default=models.F("nr_reports") / models.F("nr_invitations"),
                output_field=models.FloatField(),
            ),
            preassignment_completed_duration=ExtractDay(
                models.F("preassignment_completed_date") - models.F("submission_date")
            ),
            eic_assignment_duration=ExtractDay(
                models.F("editor_first_assigned_date")
                - models.F("preassignment_completed_date")
            ),
            first_referee_invitation_submission_duration=ExtractDay(
                models.F("first_referee_invited_date") - models.F("submission_date")
            ),
            first_referee_invitation_assignment_duration=ExtractDay(
                models.F("first_referee_invited_date")
                - models.F("editor_first_assigned_date")
            ),
        )

        match self.options.get("per_thread", None):
            case "first":
                qs = qs.filter(is_resubmission_of=None)
            case "last":
                qs = qs.filter(successor=None)
            case "all":
                pass

        return qs

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("per_thread"), css_class="col-12"),
            Div(Field("submission_date_start"), css_class="col-6"),
            Div(Field("submission_date_end"), css_class="col-6"),
        )


class ProfilePlotter(ModelFieldPlotter):
    model = Profile

    class Options(ModelFieldPlotter.Options):
        prefix = "profile_plotter_"
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("contributor__user__date_joined", ("date", "Date joined")),
            ("contributor__user__date_joined__year", ("int", "Year joined")),
            ("contributor__user__last_login", ("date", "Last login")),
            ("contributor__user__last_login__year", ("int", "Year last logged in")),
            ("topics__name", ("str", "Topics")),
            ("acad_field__name", ("str", "Academic field")),
            ("specialties__name", ("str", "Specialties")),
            ("orcid_authenticated", ("str", "ORCID authenticated")),
            ("latest_affiliation_country", ("country", "Latest affiliation country")),
            ("first_authorship_date", ("date", "First authorship date")),
            ("nr_publications", ("int", "Publications")),
            ("nr_reports", ("int", "Reports authored")),
            ("nr_submissions", ("int", "Submissions")),
        )

    def get_queryset(self) -> models.QuerySet[Profile]:
        qs = super().get_queryset()
        qs = qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(
                    profile=models.OuterRef("id"),
                )
                .order_by("-date_from")[:1]
                .values("organization__country")
            ),
            first_authorship_date=models.Subquery(
                PublicationAuthorsTable.objects.filter(profile=models.OuterRef("id"))
                .order_by("publication__publication_date")[:1]
                .values("publication__publication_date")
            ),
            nr_publications=Coalesce(
                models.Subquery(
                    PublicationAuthorsTable.objects.filter(
                        profile=models.OuterRef("id")
                    )
                    .values("profile")
                    .annotate(nr=models.Count("profile"))
                    .values("nr")
                ),
                models.Value(0),
            ),
            nr_reports=Coalesce(
                models.Subquery(
                    Report.objects.filter(author=models.OuterRef("contributor"))
                    .values("author")
                    .annotate(nr=models.Count("author"))
                    .values("nr")
                ),
                models.Value(0),
            ),
            nr_submissions=Coalesce(
                models.Subquery(
                    SubmissionAuthorProfile.objects.filter(
                        profile=models.OuterRef("id")
                    )
                    .values("profile")
                    .annotate(nr=models.Count("profile"))
                    .values("nr")
                ),
                models.Value(0),
            ),
        )

        return qs


class FellowshipPlotter(ModelFieldPlotter):
    model = Fellowship

    class Options(ModelFieldPlotter.Options):
        college = Fellowship._meta.get_field("college").formfield(required=False)
        status = Fellowship._meta.get_field("status").formfield(
            required=False,
            choices=((None, "All"),) + Fellowship.STATUS_CHOICES,
        )

        active = forms.ChoiceField(
            required=False,
            label="Active",
            choices=[
                ("all", "All"),
                ("active", "Active"),
                ("inactive", "Inactive"),
            ],
        )

        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("latest_affiliation_country", ("country", "Latest affiliation country")),
            ("latest_affiliation_name", ("str", "Latest affiliation name")),
            ("status", ("str", "Status")),
            ("start_date", ("date", "Start date")),
            ("until_date", ("date", "End date")),
            ("college__name", ("str", "College")),
            ("contributor__profile__specialties__name", ("str", "Specialties")),
        )

    def get_queryset(self) -> models.QuerySet[Fellowship]:
        qs = super().get_queryset()

        qs = qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(
                    profile=models.OuterRef("contributor__profile")
                )
                .order_by("-date_from")
                .values("organization__country")[:1]
            ),
            latest_affiliation_name=models.Subquery(
                Affiliation.objects.filter(
                    profile=models.OuterRef("contributor__profile")
                )
                .order_by("-date_from")
                .values("organization__name")[:1]
            ),
        )

        if college := self.options.get("college", None):
            qs = qs.filter(college=college)

        if status := self.options.get("status", None):
            qs = qs.filter(status=status)

        now = datetime.today()
        match self.options.get("active", "all"):
            case "active":
                qs = qs.filter(start_date__lte=now, until_date__gte=now)
            case "inactive":
                qs = qs.filter(
                    models.Q(start_date__gt=now) | models.Q(until_date__lt=now)
                )
            case "all":
                pass

        return qs

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("college"), css_class="col-12"),
            Div(Field("status"), css_class="col-6"),
            Div(Field("active"), css_class="col-6"),
        )


class PubFracPlotter(ModelFieldPlotter):
    model = PubFrac

    class Options(ModelFieldPlotter.Options):
        compensated = forms.ChoiceField(
            required=False,
            label="Compensated via subsidy",
            choices=[
                ("all", "All"),
                ("yes", "Compensated"),
                ("no", "Not compensated"),
            ],
        )
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("fraction", ("float", "Publication fraction")),
            ("organization__country", ("country", "Organization country")),
            ("organization__name", ("str", "Organization")),
            ("cf_value", ("float", "Monetary value")),
        )

    def get_queryset(self) -> models.QuerySet[PubFrac]:
        qs = super().get_queryset()

        match self.options.get("compensated", "all"):
            case "yes":
                qs = qs.filter(compensated_by__isnull=False)
            case "no":
                qs = qs.filter(compensated_by__isnull=True)
            case "all":
                pass

        return qs


class SponsorPlotter(ModelFieldPlotter):
    model = Organization
    name = "Sponsors"

    class Options(ModelFieldPlotter.Options):
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("latest_subsidy_date", ("date", "Latest subsidy date")),
            ("country", ("country", "Country")),
            ("total_subsidies", ("int", "Total subsidies")),
            ("total_amount", ("float", "Total amount")),
        )

    def get_queryset(self) -> models.QuerySet[Organization]:
        qs = super().get_queryset()
        qs = qs.annotate(
            latest_subsidy_date=models.Subquery(
                Subsidy.objects.filter(organization=models.OuterRef("id"))
                .order_by("-date_from")[:1]
                .values("date_from")
            ),
            total_subsidies=models.Subquery(
                Subsidy.objects.filter(organization=models.OuterRef("id"))
                .values("organization")
                .annotate(total=models.Count("organization"))
                .values("total")
            ),
            total_amount=models.Subquery(
                Subsidy.objects.filter(organization=models.OuterRef("id"))
                .values("organization")
                .annotate(total=models.Sum("amount"))
                .values("total")
            ),
        )

        return qs.filter(latest_subsidy_date__isnull=False)


class ReportPlotter(ModelFieldPlotter):
    model = Report

    class Options(ModelFieldPlotter.Options):
        submission_journals = forms.ModelMultipleChoiceField(
            queryset=Journal.objects.all().active(), required=False
        )
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("date_submitted", ("date", "Report date")),
            ("date_submitted__year", ("int", "Year of report")),
            ("last_invitation_creation_date", ("date", "Last invitation date")),
            (
                "report_submission_duration",
                ("int", "Report submission duration (days)"),
            ),
            (
                "latest_affiliation_country",
                ("country", "Author latest affiliation country"),
            ),
            ("invited", ("str", "Was invited")),
            ("has_attachment", ("str", "Has attachment")),
            ("anonymous", ("str", "Is anonymous")),
            ("needs_doi", ("str", "Needs DOI")),
        )

    def get_queryset(self) -> models.QuerySet[Report]:
        qs = super().get_queryset()

        qs = qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(profile=models.OuterRef("author"))
                .order_by("-date_from")
                .values("organization__country")[:1]
            ),
            has_attachment=models.Case(
                models.When(file_attachment="", then=models.Value("False")),
                default=models.Value("True"),
                output_field=models.CharField(),
            ),
            last_invitation_creation_date=models.Subquery(
                RefereeInvitation.objects.filter(
                    submission=models.OuterRef("submission"),
                    referee=models.OuterRef("author__profile"),
                    fulfilled=True,
                )
                .order_by("-date_invited")[:1]
                .values("date_invited")
            ),
            report_submission_duration=ExtractDay(
                models.F("date_submitted") - models.F("last_invitation_creation_date")
            ),
        )

        if journals := self.options.get("submission_journals", None):
            qs = qs.filter(submission__submitted_to__in=journals)

        return qs


class SubsidyPlotter(ModelFieldPlotter):
    model = Subsidy

    def get_queryset(self) -> models.QuerySet[Subsidy]:
        qs = super().get_queryset()

        qs = qs.filter(
            amount_publicly_shown=True,
        )

        return qs

    class Options(ModelFieldPlotter.Options):
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("subsidy_type", ("str", "Type")),
            ("date_from", ("date", "Start date")),
            ("date_until", ("date", "End date")),
            ("paid_on", ("date", "Paid on")),
            ("amount", ("int", "Amount")),
            ("organization__country", ("country", "Organization country")),
            ("organization__name", ("str", "Organization")),
            ("renewable", ("str", "Is renewable")),
            ("status", ("str", "Status")),
            ("collective__name", ("str", "Collective")),
            (
                "individual_budget__organization__name",
                ("str", "Individual budget funder"),
            ),
        )


class EditorialDecisionPlotter(ModelFieldPlotter):
    model = EditorialDecision

    class Options(ModelFieldPlotter.Options):
        status = EditorialDecision._meta.get_field("status").formfield(required=False)
        decision = EditorialDecision._meta.get_field("decision").formfield(
            required=False
        )
        is_alternative = forms.ChoiceField(
            required=False,
            label="Is alternative",
            choices=[
                (None, "All"),
                ("True", "Yes (Alternative)"),
                ("False", "No (Target)"),
            ],
        )
        submission_journals = forms.ModelMultipleChoiceField(
            queryset=Journal.objects.all().active(), required=False
        )
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("taken_on", ("date", "Decision date")),
            ("for_journal__name", ("str", "Decision journal")),
            ("submission__submitted_to__name", ("str", "Target journal")),
            ("decision", ("str", "Decision")),
            ("status", ("str", "Status")),
            ("submission__submission_date", ("date", "Submission date")),
            ("is_alternative", ("str", "Is alternative")),
            ("latest_recommendation_date", ("date", "Latest recommendation date")),
            ("voting_duration", ("int", "Voting duration (days)")),
        )

    def get_queryset(self) -> models.QuerySet[EditorialDecision]:
        qs = super().get_queryset()

        qs = qs.annotate(
            is_alternative=models.Case(
                models.When(
                    submission__submitted_to=models.F("for_journal"),
                    then=models.Value("False"),
                ),
                default=models.Value("True"),
                output_field=models.CharField(),
            ),
            latest_recommendation_date=models.Subquery(
                EICRecommendation.objects.filter(
                    submission=models.OuterRef("submission"),
                )
                .order_by("-date_submitted")[:1]
                .values("date_submitted")
            ),
            voting_duration=ExtractDay(
                models.F("taken_on") - models.F("latest_recommendation_date")
            ),
        )
        if is_alternative := self.options.get("is_alternative", None):
            qs = qs.filter(is_alternative=is_alternative)

        if status := self.options.get("status", None):
            qs = qs.filter(status=status)

        if decision := self.options.get("decision", None):
            qs = qs.filter(decision=decision)

        if journals := self.options.get("submission_journals", None):
            qs = qs.filter(submission__submitted_to__in=journals)

        return qs

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("status"), css_class="col-12"),
            Div(Field("decision"), css_class="col-6"),
            Div(Field("is_alternative"), css_class="col-6"),
        )


class RefereeInvitationPlotter(ModelFieldPlotter):
    model = RefereeInvitation

    class Options(ModelFieldPlotter.Options):
        accepted = forms.ChoiceField(
            required=False,
            label="Response",
            choices=[
                ("any", "Any"),
                (None, "Pending"),
                (True, "Accepted"),
                (False, "Declined"),
                ("responded", "Accepted or declined"),
            ],
        )
        fulfilled = forms.ChoiceField(
            required=False,
            label="Fulfilled",
            choices=[
                ("any", "Any"),
                (True, "Fulfilled"),
                (False, "Not fulfilled"),
            ],
        )
        cancelled = forms.ChoiceField(
            required=False,
            label="Cancelled",
            choices=[
                ("any", "Any"),
                (True, "Cancelled"),
                (False, "Not cancelled"),
            ],
        )
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("date_invited", ("date", "Invitation date")),
            ("date_responded", ("date", "Response date")),
            ("intended_delivery_date", ("date", "Intended delivery date")),
            ("accepted", ("str", "Accepted")),
            ("refusal_reason", ("str", "Refusal reason")),
            ("auto_reminders_allowed", ("str", "Auto reminders allowed")),
            ("nr_reminders", ("int", "Number of reminders")),
            ("date_last_reminded", ("date", "Last reminded")),
            ("fulfilled", ("str", "Fulfilled")),
            ("cancelled", ("str", "Cancelled")),
            ("report_response_duration", ("int", "Report response duration (days)")),
            ("has_responded_int", ("int", "Has responded")),
            ("has_delivered_int", ("int", "Has delivered")),
        )

    def get_queryset(self) -> models.QuerySet[Any]:
        qs = super().get_queryset()

        qs = qs.annotate(
            report_response_duration=ExtractDay(
                models.F("date_responded") - models.F("date_invited")
            ),
            has_responded_int=models.Q(date_responded__isnull=False),
            has_delivered_int=models.Q(fulfilled=True),
        )

        accepted = self.options.get("accepted", "any")
        if accepted == "responded":
            qs = qs.filter(accepted__isnull=False)
        elif accepted != "any":
            qs = qs.filter(accepted=accepted)

        return qs

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("accepted"), css_class="col-12"),
            Div(Field("fulfilled"), css_class="col-6"),
            Div(Field("cancelled"), css_class="col-6"),
        )
