__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from abc import ABC
from typing import TYPE_CHECKING, Any

from matplotlib.figure import Figure

from .options import BaseOptions

OptionDict = dict[str, Any]

if TYPE_CHECKING:
    from .plotkind import PlotKind


class ModelFieldPlotter(ABC):
    model: type
    date_key: str | None = None
    country_key: str | None = None
    name: str | None = None

    class Options(BaseOptions):
        prefix = "model_field_plotter_"

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

    def __str__(self):
        return self.get_name()

    def get_queryset(self):
        return self.model.objects.all()

    def get_available_plot_kinds(self):
        """Returns the plot kinds that can be used with this model field."""
        plot_kinds = []
        if self.date_key:
            plot_kinds.append("timeline")
        if self.country_key:
            plot_kinds.append("map")

        return plot_kinds

    @staticmethod
    def set_theme(theme: str):
        import matplotlib.pyplot as plt

        if theme in plt.style.available:
            plt.style.use([theme])

    def plot(self, kind: "PlotKind", options: OptionDict) -> Figure:
        """
        Create a plot of the model field according to the given kind.
        Further modify the plot according to the given options.
        """
        self.set_theme(options.get("theme", "default"))

        fig = kind.plot(plotter=self)
        fig.suptitle(options.get("title", None))

        return fig
