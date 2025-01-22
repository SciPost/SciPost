__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms
from django.db.models import Q, Avg, Count, Sum
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd

from .options import BaseOptions
from crispy_forms.layout import LayoutObject, Layout, Div, Field

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .plotter import ModelFieldPlotter, OptionDict


class PlotKind:
    """
    Generic class for a plot kind.
    """

    name: str = "Default"

    class Options(BaseOptions):
        prefix = "plot_kind_"
        pass

    def __init__(self, plotter: "ModelFieldPlotter", options: "OptionDict" = {}):
        self.plotter = plotter
        self.options = self.Options.parse_prefixed_options(options)

    @classmethod
    def class_from_name(cls, name: str):
        from graphs.graphs import ALL_PLOT_KINDS

        if cls_name := ALL_PLOT_KINDS.get(name, None):
            return cls_name

        return PlotKind

    @classmethod
    def get_name(cls) -> str:
        """Get the name of the plot kind in title case"""
        return cls.name.title()

    def __str__(self):
        return self.get_name()

    def get_figure(self, **kwargs) -> Figure:
        """
        Construct a matplotlib figure to display the plot.
        """
        return Figure(**kwargs)

    def get_data(self) -> tuple[list[int], list[Any]]:
        """
        Obtain the values to plot from the queryset.
        """
        qs = self.plotter.get_queryset()
        y = qs.values_list("id", flat=True)
        x = list(range(len(y)))
        return x, y

    def plot(self, **kwargs):
        """
        Plot the data on a the figure.
        """
        fig = self.get_figure(**kwargs.get("fig_kwargs", {}))
        ax = fig.add_subplot(111)
        ax.set_title(f"{self.get_name()} plot of {self.plotter.model.__name__}")

        try:
            x, y = self.get_data()
            ax.plot(x, y)
        except Exception as e:
            self.display_plotting_error(ax, e)

        return fig

    def display_plotting_error(self, ax: Axes, error: Exception):
        ax.text(0.5, 0.5, str(error), ha="center", va="center")
        ax.grid(False)
        ax.axis("off")

    @classmethod
    def get_plot_options_form_layout_row_content(cls) -> LayoutObject:
        return Div()


class TimelinePlot(PlotKind):
    name = "timeline"

    def plot(self, **kwargs):
        fig = super().plot(**kwargs)
        ax = fig.get_axes()[0]

        ax.set_xlabel(self.plotter.date_key)
        ax.set_ylabel(self.options.get("y_key", "id"))

        return fig

    def get_data(self):
        y_key = self.options.get("y_key", "id") or "id"

        # Filter the queryset to only include entries with a date and a y value
        query_filters = Q(
            **{
                self.plotter.date_key + "__isnull": False,
                y_key + "__isnull": False,
            }
        )
        # Filter the queryset according to the date limits if they are set
        if x_lim_min := self.options.get("x_lim_min", None):
            query_filters &= Q(**{self.plotter.date_key + "__gte": x_lim_min})
        if x_lim_max := self.options.get("x_lim_max", None):
            query_filters &= Q(**{self.plotter.date_key + "__lte": x_lim_max})

        qs = self.plotter.get_queryset()
        qs = qs.filter(query_filters)
        qs = qs.order_by(self.plotter.date_key)

        x, y = zip(*qs.values_list(self.plotter.date_key, y_key))

        return x, y

    class Options(BaseOptions):
        prefix = "timeline_plot_"
        y_key = forms.CharField(label="Y-axis key", required=False, initial="id")
        x_lim_min = forms.DateTimeField(
            label="X min",
            required=False,
            widget=forms.DateTimeInput(attrs={"type": "date"}),
        )
        x_lim_max = forms.DateTimeField(
            label="X max",
            required=False,
            widget=forms.DateTimeInput(attrs={"type": "date"}),
        )

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("y_key"), css_class="col-12"),
            Div(Field("x_lim_min"), css_class="col-6"),
            Div(Field("x_lim_max"), css_class="col-6"),
        )


class MapPlot(PlotKind):
    name = "map"

    def get_figure(self, **kwargs) -> Figure:
        from graphs.graphs import BASE_WORLD

        # Draw the world map
        fig = super().get_figure(**kwargs)
        ax = fig.add_subplot(111)
        BASE_WORLD.plot(
            ax=ax,
            color="#4161a4",
            edgecolor=ax.get_facecolor(),
            linewidth=0.25,
        )

        return fig

    def draw_colorbar(self, fig: Figure, **kwargs):
        color_bar_title = (
            self.options.get("agg_func", "count").capitalize()
            + " of "
            + self.options.get("agg_key", "id")
            + " per country"
        )

        cax = fig.add_axes([0.385, 0.2, 0.45, 0.02])
        cax.set_title(color_bar_title, fontsize="small")
        cax.tick_params(axis="x", length=2, direction="out", which="major")
        cax.tick_params(axis="x", length=1.5, direction="out", which="minor")
        cax.grid(False)

        # rectangle below the colormap with a color of `dark_blue` and a white border
        cax0 = cax.get_position()
        cax0 = fig.add_axes([cax0.x0 - 0.02, cax0.y0, 0.02 * 7 / 15, 0.02])
        cax0.set_facecolor(color="#4161a4")
        cax0.set_xlim(-1 / 2, 1 / 2)
        cax0.set_xticks([0])
        cax0.yaxis.set_visible(False)
        cax0.tick_params(axis="x", length=2, direction="out", which="major")
        cax0.tick_params(axis="x", length=1.5, direction="out", which="minor")
        cax0.grid(False)

    def plot(self, **kwargs):
        from graphs.graphs import BASE_WORLD, OKLCH
        from matplotlib.colors import LinearSegmentedColormap, LogNorm

        fig = self.get_figure(**kwargs.get("fig_kwargs", {}))
        self.draw_colorbar(fig)
        ax, cax, _ = fig.get_axes()

        ax.set_title(f"World map distribution of {self.plotter.model.__name__}")

        countries, agg = self.get_data()
        df_agg = pd.DataFrame({"ISO_A2_EH": countries, "agg": agg})
        vmax = df_agg["agg"].max()
        BASE_WORLD.merge(df_agg, left_on="ISO_A2_EH", right_on="ISO_A2_EH").plot(
            ax=ax,
            column="agg",
            legend=True,
            legend_kwds={"orientation": "horizontal"},
            cmap=LinearSegmentedColormap.from_list("custom", OKLCH),
            edgecolor=ax.get_facecolor(),
            linewidth=0.25,
            cax=cax,
            norm=LogNorm(vmax=vmax, vmin=1),
        )

        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)

        # Set the colorbar ticks to integers if < 1000, else leave intact
        labels = []
        for label, loc in zip(cax.get_xticklabels(), cax.get_xticks()):
            if loc < 1000:
                labels.append(int(loc))
            else:
                labels.append(label)

        cax.set_xticklabels(labels)

        return fig

    def get_data(self):
        """
        Return the a tuple of lists of countries and their counts.
        """
        qs = self.plotter.get_queryset()

        value_key = self.options.get("agg_key", "id") or "id"

        group_by_country_agg = qs.filter(
            Q(**{self.plotter.country_key + "__isnull": False})
        ).values(self.plotter.country_key)

        match self.options.get("agg_func", "count"):
            case "count":
                agg_func = Count
            case "sum":
                agg_func = Sum
            case "avg":
                agg_func = Avg
            case _:
                raise ValueError("Invalid aggregation function")

        group_by_country_agg = group_by_country_agg.annotate(agg=agg_func(value_key))

        countries, agg = zip(
            *group_by_country_agg.values_list(self.plotter.country_key, "agg")
        )

        # Convert the aggregated data to floats
        agg = [float(a) for a in agg]

        return countries, agg

    class Options(BaseOptions):
        prefix = "map_plot_"
        agg_func = forms.ChoiceField(
            label="Aggregation function",
            choices=[
                ("count", "Count"),
                ("sum", "Sum"),
                ("avg", "Average"),
            ],
            required=False,
            initial="count",
        )
        agg_key = forms.CharField(label="Aggregation key", initial="id", required=False)

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("agg_func"), css_class="col-6"),
            Div(Field("agg_key"), css_class="col-6"),
        )


class BarPlot(PlotKind):
    name = "bar"

    def plot(self, **kwargs):
        """
        Plot the data on a the figure.
        """
        fig = self.get_figure(**kwargs.get("fig_kwargs", {}))
        ax = fig.add_subplot(111)
        ax.set_title(f"{self.get_name()} plot of {self.plotter.model.__name__}")

        groups, vals = self.get_data()

        match self.options.get("direction", "vertical"):
            case "vertical":
                ax.bar(groups, vals)
                # Compare the width of the bars to the width of the labels
                # Rotate the labels if they are wider than the bars
                labels_overflow_bar = any(
                    label.get_window_extent().width > bar.get_window_extent().width
                    for label, bar in zip(ax.get_xticklabels(), ax.patches)
                )
                if labels_overflow_bar:
                    ax.set_xticklabels(groups, rotation=45, ha="right")
            case "horizontal":
                ax.barh(groups, vals)

        return fig

    def get_data(self):
        value_key = self.options.get("value_key", "id") or "id"
        group_by_key = self.options.get("group_by_key", "id") or "id"

        qs = self.plotter.get_queryset()
        qs = (
            qs.exclude(Q(**{group_by_key: None}))
            .values(group_by_key)
            .annotate(agg=Count(value_key))
        )

        if (order_by := self.options.get("order_by")) and (
            ordering := self.options.get("ordering")
        ):

            match order_by:
                case "group":
                    order_by = group_by_key
                case "value":
                    order_by = "agg"
                case _:
                    raise ValueError("Invalid order by value")

            ordering = "-" if ordering == "asc" else ""
            qs = qs.order_by(ordering + order_by)

        if qs.exists():
            groups, vals = zip(*qs.values_list(group_by_key, "agg"))
            return [str(group) for group in groups], vals
        else:
            return [], []

    class Options(BaseOptions):
        prefix = "bar_plot_"
        direction = forms.ChoiceField(
            label="Direction",
            choices=[
                ("vertical", "Vertical"),
                ("horizontal", "Horizontal"),
            ],
            required=False,
            initial="vertical",
            widget=forms.RadioSelect,
        )
        group_by_key = forms.CharField(
            label="Group-by key", required=False, initial="id"
        )
        value_key = forms.CharField(label="Value key", required=False, initial="id")
        order_by = forms.ChoiceField(
            label="Order by",
            choices=[
                ("group", "Group"),
                ("value", "Value"),
            ],
            required=False,
        )
        ordering = forms.ChoiceField(
            label="Ordering",
            choices=[
                ("asc", "Ascending"),
                ("desc", "Descending"),
            ],
            required=False,
        )

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("direction"), css_class="col-12"),
            Div(Field("group_by_key"), css_class="col-6"),
            Div(Field("value_key"), css_class="col-6"),
            Div(
                Div(Field("order_by"), css_class="col-6"),
                Div(Field("ordering"), css_class="col-6"),
                css_class="row",
            ),
        )
