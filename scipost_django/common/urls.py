__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from .views import htmx as htmx_views

app_name = "common"

urlpatterns = [
    path(
        "empty",
        htmx_views.empty,
        name="empty",
    ),
    path(
        "hx_dynsel/select_option/<int:content_type_id>/<int:object_id>",
        htmx_views.HXDynselSelectOptionView.as_view(),
        name="hx_dynsel_select_option",
    ),
]
