__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include
from django.views.generic import TemplateView

from . import views

app_name = "graphs"

urlpatterns = [
    path("explorer", views.explorer, name="explorer"),
    path("explorer/plot", views.PlotView.as_view(), name="explorer_plot"),
    path(
        "explorer/plot/options_form",
        views.PlotOptionsFormView.as_view(),
        name="explorer_plot_options_form",
    ),
]
