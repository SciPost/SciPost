__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from abc import ABC
from typing import TYPE_CHECKING, Any

from django import forms
from django.db import models
from django.db.models.functions import Coalesce, ExtractDay
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from colleges.models import Fellowship
from finances.models import PubFrac, Subsidy
from journals.models import Journal, Publication, PublicationAuthorsTable
from organizations.models import Organization
from profiles.models import Affiliation, Profile
from series.models import Collection
from submissions.models import Report, Submission

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
        if title := options.get("title", None):
            fig.axes[0].set_title(title)

        return fig

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Div()


class PublicationPlotter(ModelFieldPlotter):
    model = Publication
    name = "Publication"

    class Options(ModelFieldPlotter.Options):
        journals = forms.ModelChoiceField(
            queryset=Journal.objects.all().active(), required=False
        )
        collections = forms.ModelChoiceField(
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
        )

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.annotate(
            acceptance_duration=ExtractDay(
                models.F("acceptance_date") - models.F("submission_date")
            ),
            publication_duration=ExtractDay(
                models.F("publication_date") - models.F("submission_date")
            ),
        )

        if journal := self.options.get("journals", None):
            qs = qs.for_journal(journal.name)
        if collections := self.options.get("collections", None):
            qs = qs.filter(collections__in=[collections])

        return qs


class SubmissionsPlotter(ModelFieldPlotter):
    model = Submission
    date_key = "submission_date"

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
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("submission_date", ("date", "Submission date")),
            ("submission_date__year", ("int", "Year submitted")),
            ("status", ("str", "Status")),
            ("topics__name", ("str", "Topics")),
        )

    def get_queryset(self):
        qs = super().get_queryset()

        if start := self.options.get("submission_date_start", None):
            qs = qs.filter(submission_date__gte=start)
        if end := self.options.get("submission_date_end", None):
            qs = qs.filter(submission_date__lte=end)

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
            ("latest_affiliation_country", ("country", "Latest affiliation country")),
            ("first_authorship_date", ("date", "First authorship date")),
            ("total_publications", ("int", "Total publications")),
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
            total_publications=Coalesce(
                models.Subquery(
                    PublicationAuthorsTable.objects.filter(
                        profile=models.OuterRef("id")
                    )
                    .values("profile")
                    .annotate(total=models.Count("profile"))
                    .values("total")
                ),
                models.Value(0),
            ),
        )

        return qs


class FellowshipPlotter(ModelFieldPlotter):
    model = Fellowship

    class Options(ModelFieldPlotter.Options):
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("latest_affiliation_country", ("country", "Latest affiliation country")),
            ("latest_affiliation_name", ("str", "Latest affiliation name")),
        )

    def get_queryset(self) -> models.QuerySet[Fellowship]:
        qs = super().get_queryset()

        return qs.annotate(
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


class PubFracPlotter(ModelFieldPlotter):
    model = PubFrac

    class Options(ModelFieldPlotter.Options):
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("fraction", ("float", "Publication fraction")),
            ("organization__country", ("country", "Organization country")),
            ("organization__name", ("str", "Organization")),
        )


class RefereePlotter(ModelFieldPlotter):
    model = Profile
    name = "Referees"

    class Options(ModelFieldPlotter.Options):
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("latest_report_date", ("date", "Latest report date")),
            ("latest_report_date_year", ("int", "Year of latest report")),
            ("latest_affiliation_country", ("country", "Latest affiliation country")),
        )

    def get_queryset(self) -> models.QuerySet[Profile]:
        qs = super().get_queryset()
        return qs.annotate(
            latest_report_date=models.Subquery(
                Report.objects.filter(author=models.OuterRef("contributor"))
                .order_by("-created")[:1]
                .values("created")
            ),
            latest_report_date_year=models.Subquery(
                Report.objects.filter(author=models.OuterRef("contributor"))
                .order_by("-created")[:1]
                .values("created__year")
            ),
            latest_affiliation_country=models.Case(
                models.When(
                    latest_report_date__isnull=False,
                    then=models.Subquery(
                        Affiliation.objects.filter(
                            profile=models.OuterRef("id"),
                        )
                        .order_by("-date_from")[:1]
                        .values("organization__country")
                    ),
                ),
                default=None,
            ),
        )


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
        model_fields = ModelFieldPlotter.Options.model_fields + (
            ("created", ("date", "Report date")),
            ("created__year", ("int", "Year of report")),
            (
                "latest_affiliation_country",
                ("country", "Author latest affiliation country"),
            ),
        )

    def get_queryset(self) -> models.QuerySet[Report]:
        qs = super().get_queryset()

        return qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(profile=models.OuterRef("author"))
                .order_by("-date_from")
                .values("organization__country")[:1]
            )
        )


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
            ("date_from", ("date", "Start date")),
            ("date_until", ("date", "End date")),
            ("amount", ("int", "Amount")),
            ("organization__country", ("country", "Organization country")),
            ("organization__name", ("str", "Organization")),
        )
