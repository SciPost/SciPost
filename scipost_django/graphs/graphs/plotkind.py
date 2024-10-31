__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django import forms
from django.db.models import Q, Count
from matplotlib.figure import Figure
import pandas as pd

from .options import BaseOptions

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .plotter import ModelFieldPlotter, OptionDict


class PlotKind:
    """
    Generic class for a plot kind.
    """

    name: str

    class Options(BaseOptions):
        prefix = "plot_kind_"
        pass

    def __init__(self, options: "OptionDict" = {}):
        self.options = self.Options.parse_prefixed_options(options)

    @classmethod
    def from_name(cls, name: str, *args, **kwargs):
        from graphs.graphs import ALL_PLOT_KINDS

        if cls_name := ALL_PLOT_KINDS.get(name, None):
            return cls_name(*args, **kwargs)

    @classmethod
    def get_name(cls) -> str:
        return cls.name.title()

    def __str__(self):
        return self.get_name()

    def get_figure(self, **kwargs) -> Figure:
        """
        Construct a matplotlib figure to display the plot.
        """
        return Figure(**kwargs)

    def get_data(self, plotter: "ModelFieldPlotter") -> tuple[list[int], list[Any]]:
        """
        Obtain the values to plot from the queryset.
        """
        qs = plotter.get_queryset()
        y = qs.values_list("id", flat=True)
        x = list(range(len(y)))
        return x, y

    def plot(self, plotter: "ModelFieldPlotter"):
        """
        Plot the data on a the figure.
        """
        fig = self.get_figure()
        ax = fig.add_subplot(111)
        ax.set_title(f"{self.get_name().title()} plot of {plotter.model.__name__}")

        x, y = self.get_data(plotter)
        ax.plot(x, y)
        return fig


class TimelinePlot(PlotKind):
    name = "timeline"

    def plot(self, plotter: "ModelFieldPlotter"):
        fig = super().plot(plotter)
        ax = fig.get_axes()[0]

        ax.set_xlabel(plotter.date_key)
        ax.set_ylabel(self.options.get("y_key", "id"))

        return fig

    def get_data(self, plotter: "ModelFieldPlotter", **kwargs):
        y_key = self.options.get("y_key", "id")

        # Filter the queryset according to the date limits if they are set
        query_filters = Q()
        if x_lim_min := self.options.get("x_lim_min", None):
            query_filters &= Q(**{plotter.date_key + "__gte": x_lim_min})
        if x_lim_max := self.options.get("x_lim_max", None):
            query_filters &= Q(**{plotter.date_key + "__lte": x_lim_max})

        qs = plotter.get_queryset()
        qs = qs.filter(query_filters)

        x, y = zip(*qs.values_list(plotter.date_key, y_key))

        return x, y

    class Options(BaseOptions):
        prefix = PlotKind.Options.prefix
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
        cax.set_title("Counts", fontsize="small")
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

    def plot(self, plotter: "ModelFieldPlotter"):
        from graphs.graphs import BASE_WORLD, OKLCH
        from matplotlib.colors import LinearSegmentedColormap, LogNorm

        fig = self.get_figure()
        self.draw_colorbar(fig)
        ax, cax, _ = fig.get_axes()

        countries, count = self.get_data(plotter)
        df_counts = pd.DataFrame({"ISO_A2_EH": countries, "count": count})
        vmax = df_counts["count"].max()
        BASE_WORLD.merge(df_counts, left_on="ISO_A2_EH", right_on="ISO_A2_EH").plot(
            ax=ax,
            column="count",
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

        cax.xaxis.set_ticklabels(f"{int(x)}" for x in cax.xaxis.get_ticklocs())

        return fig

    def get_data(self, plotter: "ModelFieldPlotter", **kwargs):
        qs = plotter.get_queryset()
        count_key = self.options.get("count_key", "id")
        group_by_country_count = (
            qs.filter(Q(**{plotter.country_key + "__isnull": False}))
            .values(plotter.country_key)
            .annotate(count=Count(count_key))
        )

        countries, count = zip(
            *group_by_country_count.values_list(plotter.country_key, "count")
        )
        return countries, count

