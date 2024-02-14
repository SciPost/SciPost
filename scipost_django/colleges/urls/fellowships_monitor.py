__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from ..views import fellowships_monitor as views

app_name = "fellowships_monitor"


urlpatterns = [  # Building on: /colleges/fellowships_monitor/
    path(
        "",
        views.fellowships_monitor,
        name="monitor",
    ),
    path(
        "_hx_table",
        views._hx_table,
        name="_hx_table",
    ),
    path(
        "_hx_search_form/<str:filter_set>",
        views._hx_search_form,
        name="_hx_search_form",
    ),
]
