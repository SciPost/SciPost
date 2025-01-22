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
        raise NotImplementedError("Please select a plot kind.")

    def plot(self, **kwargs):
        """
        Plot the data on a the figure.
        """
        fig = self.get_figure(**kwargs.get("fig_kwargs", {}))
        ax = fig.add_subplot(111)

        try:
            x, y = self.get_data()
            ax.plot(x, y)
        except Exception as e:
            PlotKind.display_plotting_error(ax, e)
            return fig

        ax.set_title(f"{self.get_name()} plot of {self.plotter.model.__name__}")

        return fig

    @staticmethod
    def display_plotting_error(ax: Axes, error: Exception):
        MAX_CHAR_WIDTH = 80
        str_error = str(error)
        error_lines = [
            str_error[i : i + MAX_CHAR_WIDTH]
            for i in range(0, len(str_error), MAX_CHAR_WIDTH)
        ]
        error_text = "\n".join(error_lines)

        ax.text(0.5, 0.5, error_text, ha="center", va="center")
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

        if timeline_key_label := self.plotter.get_model_field_display(
            self.options.get("timeline_key", "")
        ):
            ax.set_xlabel(timeline_key_label)

        if value_key_label := self.plotter.get_model_field_display(
            self.options.get("value_key", "")
        ):
            ax.set_ylabel(value_key_label)

        return fig

    def get_data(self):
        timeline_key = self.options.get("timeline_key", "id") or "id"
        value_key = self.options.get("value_key", "id") or "id"

        # Filter the queryset to only include entries with a date and a y value
        query_filters = Q(
            **{
                timeline_key + "__isnull": False,
                value_key + "__isnull": False,
            }
        )
        # Filter the queryset according to the date limits if they are set
        if x_lim_min := self.options.get("x_lim_min", None):
            query_filters &= Q(**{timeline_key + "__gte": x_lim_min})
        if x_lim_max := self.options.get("x_lim_max", None):
            query_filters &= Q(**{timeline_key + "__lte": x_lim_max})

        qs = self.plotter.get_queryset()
        qs = qs.filter(query_filters)
        qs = qs.order_by(timeline_key)

        x, y = zip(*qs.values_list(timeline_key, value_key))

        return x, y

    class Options(BaseOptions):
        prefix = "timeline_plot_"
        timeline_key = forms.ChoiceField(
            label="Timeline key", initial="id", required=False, choices=[]
        )
        value_key = forms.ChoiceField(
            label="Value key", initial="id", required=False, choices=[]
        )
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
            Div(Field("timeline_key"), css_class="col-12"),
            Div(Field("x_lim_min"), css_class="col-6"),
            Div(Field("x_lim_max"), css_class="col-6"),
            Div(Field("value_key"), css_class="col-12"),
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
        cax = fig.add_axes([0.385, 0.2, 0.45, 0.02])
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

        agg_func = self.options.get("agg_func", "count")
        value_key_display = self.plotter.get_model_field_display(
            self.options.get("value_key", "")
        )
        country_key_display = (
            self.plotter.get_model_field_display(self.options.get("country_key", ""))
            or "country"
        )
        if agg_func == "count":
            plot_title = "{model} per {country}"
        else:
            plot_title = "{agg_func} of {model}' {value_key_display} per {country}"

        plot_title = plot_title.format(
            model=self.plotter.model._meta.verbose_name_plural,
            agg_func=agg_func,
            value_key_display=value_key_display,
            country=country_key_display,
        ).capitalize()

        ax.set_title(plot_title)
        color_plot_title, _ = plot_title.split(" per ")
        cax.set_title(color_plot_title, fontsize="small")

        try:
            countries, agg = self.get_data()
        except Exception as e:
            PlotKind.display_plotting_error(ax, e)
            return fig

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

        value_key = self.options.get("value_key", "id") or "id"
        country_key = self.options.get("country_key")

        if country_key is None:
            raise ValueError("Country key not set. Cannot plot a map.")

        match self.options.get("agg_func", "count"):
            case "count":
                agg_func = Count("id")
            case "sum":
                agg_func = Sum(value_key)
            case "avg":
                agg_func = Avg(value_key)
            case _:
                raise ValueError("Invalid aggregation function")

        group_by_country_agg = (
            qs.filter(Q(**{country_key + "__isnull": False}))
            .values(country_key)
            .annotate(agg=agg_func)
        )

        countries, agg = zip(*group_by_country_agg.values_list(country_key, "agg"))

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
        value_key = forms.ChoiceField(label="Value key", required=False, choices=[])
        country_key = forms.ChoiceField(label="Country key", required=False, choices=[])

    @classmethod
    def get_plot_options_form_layout_row_content(cls):
        return Layout(
            Div(Field("country_key"), css_class="col-12"),
            Div(Field("agg_func"), css_class="col-6"),
            Div(Field("value_key"), css_class="col-6"),
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

        direction = self.options.get("direction", "vertical") or "vertical"
        if group_key_label := self.plotter.get_model_field_display(
            self.options.get("group_key", "")
        ):
            if direction == "vertical":
                ax.set_xlabel(group_key_label)
            elif direction == "horizontal":
                ax.set_ylabel(group_key_label)

        if value_key_label := self.plotter.get_model_field_display(
            self.options.get("value_key", "")
        ):
            if direction == "vertical":
                ax.set_ylabel(value_key_label)
            elif direction == "horizontal":
                ax.set_xlabel(value_key_label)

        try:
            groups, vals = self.get_data()
        except Exception as e:
            PlotKind.display_plotting_error(ax, e)
            return fig

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
        group_key = self.options.get("group_key")
        direction = self.options.get("direction", "vertical") or "vertical"

        if group_key is None:
            raise ValueError("Group key not set. Cannot plot a bar plot.")
        if group_key == "id":
            raise ValueError("Group key cannot be the primary key of the model.")

        match self.options.get("agg_func", "count"):
            case "count":
                agg_func = Count("id")
            case "sum":
                agg_func = Sum(value_key)
            case "avg":
                agg_func = Avg(value_key)
            case _:
                raise ValueError("Invalid aggregation function")

        qs = (
            self.plotter.get_queryset()
            .values(group_key)
            .annotate(agg=agg_func)
            .exclude(Q(**{group_key: None}) | Q(agg=None))
        )

        if (order_by := self.options.get("order_by")) and (
            ordering := self.options.get("ordering")
        ):

            match order_by:
                case "group":
                    order_by = group_key
                case "value":
                    order_by = "agg"
                case _:
                    raise ValueError("Invalid order by value")

            # Flip roles of ascending and descending if the direction is horizontal
            # by leveraging a Z_2 group action (sign flip)
            ordering_sign = -1 if ordering == "desc" else 1
            direction_sign = -1 if direction == "horizontal" else 1
            ordering = "-" if ordering_sign * direction_sign == -1 else ""
            qs = qs.order_by(ordering + order_by)

        if qs.exists():
            groups, vals = zip(*qs.values_list(group_key, "agg"))
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
        group_key = forms.ChoiceField(
            label="Group by key", required=False, initial="id", choices=[]
        )
        value_key = forms.ChoiceField(
            label="Value key", required=False, initial="id", choices=[]
        )
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
            Div(
                Field("direction", css_class="d-flex flex-row gap-3"),
                css_class="col-12",
            ),
            Div(Field("group_key"), css_class="col-12"),
            Div(Field("agg_func"), css_class="col-6"),
            Div(Field("value_key"), css_class="col-6"),
            Div(
                Div(
                    Div(Field("order_by"), css_class="col-6"),
                    Div(Field("ordering"), css_class="col-6"),
                    css_class="row",
                ),
                css_class="col-12",
            ),
        )
