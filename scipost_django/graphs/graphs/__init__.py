__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from .plotter import *
from .plotkind import *

from pathlib import Path

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

GRAPHS_APP_DIR = Path(__file__).resolve().parent.parent
ALL_MPL_THEMES = {
    theme.stem: theme for theme in Path(GRAPHS_APP_DIR, "mpl_themes").iterdir()
}
AVAILABLE_MPL_THEMES = {
    k: v for k, v in ALL_MPL_THEMES.items() if not k.startswith("_")
}
