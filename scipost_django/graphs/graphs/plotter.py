__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from abc import ABC
from datetime import date
from typing import TYPE_CHECKING, Any

from django import forms
from django.db import models
from django.db.models.functions import Coalesce, ExtractDay
from django.utils.timezone import datetime
from django_countries.fields import Country as country

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from colleges.models import Fellowship
from finances.models import PubFrac, Subsidy
from journals.models import Journal, Publication, PublicationAuthorsTable
from ontology.models.specialty import Specialty
from organizations.models import Organization
from profiles.models import Affiliation, Profile
from series.models import Collection
from submissions.constants import EIC_REC_PUBLISH, EIC_REC_REJECT
from submissions.models import Report, Submission
from submissions.models.assignment import EditorialAssignment
from submissions.models.decision import EditorialDecision
from submissions.models.recommendation import EICRecommendation
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.submission import SubmissionAuthorProfile, SubmissionEvent

from .options import BaseOptions, GraphModelField as GMF

from crispy_forms.layout import Layout, Div, Field

OptionDict = dict[str, Any]

if TYPE_CHECKING:
    from .plotkind import PlotKind


class ModelFieldPlotter(ABC):
    model: type
    name: str | None = None

    class Options(BaseOptions):
        prefix = "model_field_plotter_"
        model_fields: tuple[GMF, ...] = (GMF("id", "ID", int),)

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

    def get_model_field(self, key: str | None) -> GMF | None:
        if (
            key is not None
            and (options := getattr(self, "Options", None))
            and (model_fields := getattr(options, "model_fields", None))
        ):
            model_fields: tuple[GMF, ...]
            for field in model_fields:
                if field.name == key:
                    return field

            return None

    def __str__(self):
        return self.get_name()

    def get_queryset(self) -> models.QuerySet[Any]:
        qs = self.model.objects.all()
        return qs

    def get_available_plot_kinds(self) -> list[str]:
        """Returns the plot kinds that can be used with this model field."""
        try:
            model_fields_types = [field.type for field in self.Options.model_fields]
        except AttributeError:
            return []

        plot_kinds: list[str] = []
        if date in model_fields_types or datetime in model_fields_types:
            plot_kinds.append("timeline")
        if country in model_fields_types:
            plot_kinds.append("map")
        if int in model_fields_types or float in model_fields_types:
            plot_kinds.append("bar")
            plot_kinds.append("histogram")

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

        if options.get("hide_x_label", True):
            main_ax.set_xlabel("")
            main_ax.set_xticks([])
            main_ax.set_xticklabels([])

        if options.get("hide_y_label", True):
            main_ax.set_ylabel("")
            main_ax.set_yticks([])
            main_ax.set_yticklabels([])

        if x_label := options.get("x_label", main_ax.get_xlabel()):
            main_ax.set_xlabel(x_label)

        if y_label := options.get("y_label", main_ax.get_ylabel()):
            main_ax.set_ylabel(y_label)

        if options.get("hide_grid", False):
            main_ax.grid(False)

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
            GMF("submission_date", "Submission date", date),
            GMF("submission_date__year", "Year submitted", int),
            GMF("publication_date", "Publication date", date),
            GMF("publication_date__year", "Year published", int),
            GMF("acceptance_date", "Acceptance date", date),
            GMF("acceptance_date__year", "Year accepted", int),
            GMF("acceptance_duration", "Acceptance duration (days)", int),
            GMF("publication_duration", "Publication duration (days)", int),
            GMF("production_duration", "Production duration (days)", int),
            GMF("nr_versions", "Number of versions", int),
            GMF("acad_field__name", "Academic field", str),
            GMF("specialties__name", "Specialties", str),
            GMF("number_of_citations", "Number of citations", int),
            GMF("journal_name", "Journal name", str),
        )

    def get_queryset(self):
        qs = super().get_queryset()

        qs = (
            qs.all()
            .annot_journal_name()
            .annotate(
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
            GMF("submission_date", "Submission date", date),
            GMF("submission_date__year", "Year submitted", int),
            GMF("status", "Status", str),
            GMF("final_thread_status", "Final status (in thread)", str),
            GMF("topics__name", "Topics", str),
            GMF("acad_field__name", "Academic field", str),
            GMF("specialties__name", "Specialties", str),
            GMF("submitted_to__name", "Target journal", str),
            GMF("proceedings__event_suffix", "Proceedings", str),
            GMF("nr_invitations", "Number of invitations", int),
            GMF("nr_reports", "Number of reports", int),
            GMF("report_turnover", "Report turnover", float),
            GMF("preassignment_completed_date", "Preassignment completed date", date),
            GMF("editor_first_assigned_date", "Editor first assigned date", date),
            GMF("first_referee_invited_date", "First referee invited date", date),
            GMF("withdrawal_date", "Withdrawal date", date),
            GMF(
                "preassignment_completed_duration",
                "Preassignment duration (days)",
                int,
            ),
            GMF("eic_assignment_duration", "EIC assignment duration (days)", int),
            GMF(
                "first_referee_invitation_submission_duration",
                "Submission to first ref. invitation sent (days)",
                int,
            ),
            GMF(
                "first_referee_invitation_assignment_duration",
                "EIC assignment to first ref. invitation sent (days)",
                int,
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
            final_thread_status=models.Subquery(
                Submission.objects.filter(thread_hash=models.OuterRef("thread_hash"))
                .order_by("-submission_date")
                .values("status")[:1]
            ),
            preassignment_completed_date=models.Subquery(
                SubmissionEvent.objects.filter(
                    submission=models.OuterRef("id"),
                    text__regex=r"Submission (passed|failed|completed) pre(-screening|assignment)\.( \[Retroactively inferred from mail log\])?",
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
            GMF("contributor__dbuser__date_joined", "Date joined", date),
            GMF("contributor__dbuser__date_joined__year", "Year joined", int),
            GMF("contributor__dbuser__last_login", "Last login", date),
            GMF("contributor__dbuser__last_login__year", "Year last logged in", int),
            GMF("topics__name", "Topics", str),
            GMF("acad_field__name", "Academic field", str),
            GMF("specialties__name", "Specialties", str),
            GMF("orcid_authenticated", "ORCID authenticated", str),
            GMF("latest_affiliation_country", "Latest affiliation country", country),
            GMF("first_authorship_date", "First authorship date", date),
            GMF("nr_publications", "Publications", int),
            GMF("nr_reports", "Reports authored", int),
            GMF("nr_submissions", "Submissions", int),
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
            GMF("contributor__profile__full_name", "Fellow", str),
            GMF("latest_affiliation_country", "Latest affiliation country", country),
            GMF("latest_affiliation_name", "Latest affiliation name", str),
            GMF("status", "Status", str),
            GMF("start_date", "Start date", date),
            GMF("until_date", "End date", date),
            GMF("college__name", "College", str),
            GMF("contributor__profile__specialties__name", "Specialties", str),
            GMF("nr_threads_handled", "Number of threads handled", int),
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
            nr_threads_handled=Coalesce(
                models.Subquery(
                    EditorialAssignment.objects.accepted()
                    .filter(to=models.OuterRef("contributor"))
                    .values("to")
                    .annotate(
                        count=models.Count("submission__thread_hash", distinct=True)
                    )
                    .values("count")[:1]
                ),
                models.Value(0),
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
            GMF("fraction", "Publication fraction", float),
            GMF("organization__country", "Organization country", country),
            GMF("organization__name", "Organization", str),
            GMF("cf_value", "Monetary value", float),
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
            GMF("latest_subsidy_date", "Latest subsidy date", date),
            GMF("country", "Country", country),
            GMF("total_subsidies", "Total subsidies", int),
            GMF("total_amount", "Total amount", float),
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
            GMF("date_submitted", "Report date", date),
            GMF("date_submitted__year", "Year of report", int),
            GMF("last_invitation_creation_date", "Last invitation date", date),
            GMF("report_submission_duration", "Report submission duration (days)", int),
            GMF(
                "latest_affiliation_country",
                "Author latest affiliation country",
                country,
            ),
            GMF("invited", "Was invited", str),
            GMF("has_attachment", "Has attachment", str),
            GMF("anonymous", "Is anonymous", str),
            GMF("needs_doi", "Needs DOI", str),
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
            GMF("subsidy_type", "Type", str),
            GMF("date_from", "Start date", date),
            GMF("date_until", "End date", date),
            GMF("paid_on", "Paid on", date),
            GMF("amount", "Amount", int),
            GMF("organization__country", "Organization country", country),
            GMF("organization__name", "Organization", str),
            GMF("renewable", "Is renewable", str),
            GMF("status", "Status", str),
            GMF("collective__name", "Collective", str),
            GMF(
                "individual_budget__organization__name", "Individual budget funder", str
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
            GMF("taken_on", "Decision date", date),
            GMF("for_journal__name", "Decision journal", str),
            GMF("submission__submitted_to__name", "Target journal", str),
            GMF("decision", "Decision", str),
            GMF("status", "Status", str),
            GMF("submission__submission_date", "Submission date", date),
            GMF("is_alternative", "Is alternative", str),
            GMF("latest_recommendation_date", "Latest recommendation date", date),
            GMF("voting_duration", "Voting duration (days)", int),
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
            GMF("date_invited", "Invitation date", date),
            GMF("date_invited__year", "Year invited", int),
            GMF("date_responded", "Response date", date),
            GMF("date_responded__year", "Year responded", int),
            GMF("intended_delivery_date", "Intended delivery date", date),
            GMF("accepted", "Accepted", str),
            GMF("refusal_reason", "Refusal reason", str),
            GMF("auto_reminders_allowed", "Auto reminders allowed", str),
            GMF("nr_reminders", "Number of reminders", int),
            GMF("date_last_reminded", "Last reminded", date),
            GMF("fulfilled", "Fulfilled", str),
            GMF("cancelled", "Cancelled", str),
            GMF("report_response_duration", "Report response duration (days)", int),
            GMF("has_responded_int", "Has responded", int),
            GMF("has_delivered_int", "Has delivered", int),
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


class EditorialAssignmentPlotter(ModelFieldPlotter):
    model = EditorialAssignment

    class Options(ModelFieldPlotter.Options):
        submission_journals = forms.ModelMultipleChoiceField(
            queryset=Journal.objects.all().active(),
            required=False,
            label="Target journal",
        )
        per_thread = forms.ChoiceField(
            required=False,
            label="Keep Submissions of thread",
            choices=[("all", "All"), ("first", "First"), ("last", "Last")],
        )
        statuses = forms.MultipleChoiceField(
            required=False,
            choices=(
                *(
                    (status, display)
                    for status, display in EditorialAssignment.ASSIGNMENT_STATUSES
                    if status
                    in [
                        EditorialAssignment.STATUS_ACCEPTED,
                        EditorialAssignment.STATUS_COMPLETED,
                        EditorialAssignment.STATUS_DECLINED,
                        EditorialAssignment.STATUS_DEPRECATED,
                    ]
                ),
            ),
        )
        assignment_date_start = forms.DateField(
            required=False,
            label="Assigned after",
            widget=forms.DateInput(attrs={"type": "date"}),
        )
        assignment_date_end = forms.DateField(
            required=False,
            label="Assigned before",
            widget=forms.DateInput(attrs={"type": "date"}),
        )

        model_fields = ModelFieldPlotter.Options.model_fields + (
            GMF("date_answered", "Assignment date", date),
            GMF("date_answered__year", "Assignment year", int),
            GMF("submission__submitted_to__name", "Target journal", str),
            GMF("status", "Status", str),
            GMF("decision", "Editorial decision", str),
            GMF("to__profile__full_name", "Editor", str),
            GMF("to__profile__specialties__name", "Specialties", str),
            GMF("to__profile__acad_field__name", "Academic field", str),
            GMF("to__profile__latest_affiliation_country", "Country", country),
        )

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("per_thread"), css_class="col-12"),
            Div(Field("submission_journals"), css_class="col-12"),
            Div(Field("statuses"), css_class="col-12"),
            Div(Field("assignment_date_start"), css_class="col-6"),
            Div(Field("assignment_date_end"), css_class="col-6"),
        )

    def get_queryset(self) -> models.QuerySet[EditorialAssignment]:
        qs = (
            super()
            .get_queryset()
            .annotate(
                decision_int=models.Subquery(
                    EditorialDecision.objects.filter(
                        submission__thread_hash=models.OuterRef(
                            "submission__thread_hash"
                        ),
                    )
                    .nondeprecated()
                    .order_by("-submission__submission_date", "-version")
                    .values("decision")[:1]
                ),
                decision=models.Case(
                    models.When(
                        decision_int=EIC_REC_PUBLISH,
                        then=models.Value("Publish"),
                    ),
                    models.When(
                        decision_int=EIC_REC_REJECT,
                        then=models.Value("Reject"),
                    ),
                    default=models.Value("No decision"),
                ),
            )
        )

        match self.options.get("per_thread", "all"):
            case "first":
                qs = qs.filter(submission__is_resubmission_of=None)
            case "last":
                qs = qs.filter(submission__successor=None)
            case "all":
                pass

        if journals := self.options.get("submission_journals", None):
            qs = qs.filter(submission__submitted_to__in=journals)

        if statuses := self.options.get("statuses", None):
            qs = qs.filter(status__in=statuses)

        if start := self.options.get("assignment_date_start", None):
            qs = qs.filter(date_answered__gte=start)

        if end := self.options.get("assignment_date_end", None):
            qs = qs.filter(date_answered__lte=end)

        return qs
