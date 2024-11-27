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


import geopandas as gpd

world_map_file_URL = (
    "http://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
)
BASE_WORLD = gpd.read_file(world_map_file_URL)

columns_to_keep = ["NAME", "CONTINENT", "TYPE", "LEVEL", "ISO_A2_EH", "geometry"]
BASE_WORLD = BASE_WORLD[columns_to_keep]
BASE_WORLD = BASE_WORLD[BASE_WORLD["CONTINENT"] != "Antarctica"]

OKLCH = [
    "#6783c1",
    "#8980c9",
    "#ab7cc6",
    "#ca79b7",
    "#e37a9d",
    "#f47f7b",
    "#fb8d52",
    "#f5a119",
]
