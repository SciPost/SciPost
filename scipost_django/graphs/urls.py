__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include
from django.views.generic import TemplateView

from . import views

app_name = "graphs"

urlpatterns = [
    path("", views.graphs, name="graphs"),
    path("plot", views.PlotView.as_view(), name="plot"),
    path(
        "plot/options_form",
        views.PlotOptionsFormView.as_view(),
        name="plot_options_form",
    ),
]
