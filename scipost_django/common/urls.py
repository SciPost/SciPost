__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from .views import htmx as htmx_views
from .views import object_merger as merger_views

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
    path(
        "object_merger/<int:content_type_id>/",
        include(
            [
                path(
                    "potential_duplicates",
                    htmx_views.empty,
                    name="hx_potential_duplicates",
                ),
                path(
                    "<int:object_a_id>/<int:object_b_id>/",
                    include(
                        [
                            path(
                                "compare",
                                merger_views.HXCompareView.as_view(),
                                name="object_merger_compare",
                            ),
                            path(
                                "merge",
                                merger_views.HXMergeView.as_view(),
                                name="object_merger_merge",
                            ),
                            path(
                                "mark_not_duplicate",
                                htmx_views.empty,
                                name="object_merger_mark_not_duplicate",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
