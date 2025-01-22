__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from abc import ABC
from typing import TYPE_CHECKING, Any

from django import forms
from django.db import models
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

from crispy_forms.layout import Div

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

    @classmethod
    def get_model_field_display(cls, key: str) -> str | None:
        if (options := getattr(cls, "Options", None)) and (
            model_fields := getattr(options, "model_fields", None)
        ):
            for field, (_, value_display) in model_fields:
                if field == key:
                    return value_display

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
    date_key = "publication_date"

    class Options(ModelFieldPlotter.Options):
        journals = forms.ModelChoiceField(
            queryset=Journal.objects.all().active(), required=False
        )
        collections = forms.ModelChoiceField(
            queryset=Collection.objects.all(), required=False
        )

    def get_queryset(self):
        qs = super().get_queryset()
        if journal := self.options.get("journals", None):
            qs = qs.for_journal(journal.name)
        if collections := self.options.get("collections", None):
            qs = qs.filter(collections__in=[collections])

        return qs


class SubmissionsPlotter(ModelFieldPlotter):
    model = Submission
    date_key = "submission_date"


class ProfilePlotter(ModelFieldPlotter):
    model = Profile
    date_key = "contributor__user__date_joined"
    country_key = "latest_affiliation_country"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(
                    profile=models.OuterRef("id"),
                )
                .order_by("-date_from")[:1]
                .values("organization__country")
            )
        )


class FellowshipPlotter(ModelFieldPlotter):
    model = Fellowship
    date_key = "start_date"
    country_key = "latest_affiliation_country"

    def get_queryset(self) -> models.QuerySet[Fellowship]:
        qs = super().get_queryset()

        return qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(
                    profile=models.OuterRef("contributor__profile")
                )
                .order_by("-date_from")
                .values("organization__country")[:1]
            )
        )


class PubFracPlotter(ModelFieldPlotter):
    model = PubFrac
    country_key = "organization__country"


class RefereePlotter(ModelFieldPlotter):
    model = Profile
    name = "Referees"
    date_key = "latest_report_date"
    country_key = "referee_country"

    def get_queryset(self) -> models.QuerySet[Profile]:
        qs = super().get_queryset()
        return qs.annotate(
            latest_report_date=models.Subquery(
                Report.objects.filter(author=models.OuterRef("contributor"))
                .order_by("-created")[:1]
                .values("created")
            ),
            referee_country=models.Case(
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


class AuthorPlotter(ModelFieldPlotter):
    model = Profile
    name = "Published Authors"
    date_key = "first_authorship_date"
    country_key = "author_country"

    def get_queryset(self) -> models.QuerySet[Profile]:
        qs = super().get_queryset()
        return qs.annotate(
            first_authorship_date=models.Subquery(
                PublicationAuthorsTable.objects.filter(profile=models.OuterRef("id"))
                .order_by("publication__publication_date")[:1]
                .values("publication__publication_date")
            ),
            author_country=models.Case(
                models.When(
                    first_authorship_date__isnull=False,
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
    date_key = "latest_subsidy"
    country_key = "country"

    def get_queryset(self) -> models.QuerySet[Organization]:
        qs = super().get_queryset()
        return qs.annotate(
            latest_subsidy=models.Subquery(
                Subsidy.objects.filter(organization=models.OuterRef("id"))
                .order_by("-date_from")[:1]
                .values("date_from")
            ),
        ).filter(latest_subsidy__isnull=False)


class ReportPlotter(ModelFieldPlotter):
    model = Report
    date_key = "created"
    country_key = "latest_affiliation_country"

    def get_queryset(self) -> models.QuerySet[Report]:
        qs = super().get_queryset()

        return qs.annotate(
            latest_affiliation_country=models.Subquery(
                Affiliation.objects.filter(profile=models.OuterRef("author"))
                .order_by("-date_from")
                .values("organization__country")[:1]
            )
        )
