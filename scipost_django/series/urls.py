__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include

from . import views


app_name = "series"

urlpatterns = [
    path("", views.SeriesListView.as_view(), name="series"),
    path("<slug:slug>", views.SeriesDetailView.as_view(), name="series_detail"),
    path(
        "collection/<slug:slug>/",
        include(
            [
                path(
                    "", views.CollectionDetailView.as_view(), name="collection_detail"
                ),
                path(
                    "_hx_collection_expected_authors",
                    views._hx_collection_expected_authors,
                    name="_hx_collection_expected_authors",
                ),
                path(
                    "_hx_collection_expected_author_action/<int:profile_id>/<str:action>",
                    views._hx_collection_expected_author_action,
                    name="_hx_collection_expected_author_action",
                ),
                path(
                    "_hx_collection_publications",
                    views._hx_collection_publications,
                    name="_hx_collection_publications",
                ),
                path(
                    "_hx_collection_publication_action/<publication_doi_label:doi_label>/<str:action>",
                    views._hx_collection_publication_action,
                    name="_hx_collection_publication_action",
                ),
            ]
        ),
    ),
]
