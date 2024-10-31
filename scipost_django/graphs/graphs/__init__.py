from .plotter import *
from .plotkind import *

ALL_PLOTTERS = {
    cls.get_name(): cls
    for cls in globals().values()
    if isinstance(cls, type)
    and issubclass(cls, ModelFieldPlotter)
    and cls is not ModelFieldPlotter
}


ALL_PLOT_KINDS = {
    cls.name: cls
    for cls in globals().values()
    if isinstance(cls, type) and issubclass(cls, PlotKind) and cls is not PlotKind
}
