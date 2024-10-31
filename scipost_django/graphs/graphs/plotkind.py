__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from matplotlib.figure import Figure

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
        x, y = zip(*plotter.get_queryset().values_list(plotter.date_key, y_key))

        return x, y

    class Options(BaseOptions):
        prefix = PlotKind.Options.prefix
        y_key = forms.CharField(label="Y-axis key", required=False, initial="id")
