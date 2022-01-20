__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views


app_name = 'series'

urlpatterns = [
    path(
        '',
        views.SeriesListView.as_view(),
        name='series'
    ),
    path(
        '<slug:slug>',
        views.SeriesDetailView.as_view(),
        name='series_detail'
    ),
    path(
        'collection/<slug:slug>',
         views.CollectionDetailView.as_view(),
         name='collection_detail'
    ),
    path(
        'collection/<slug:slug>/add_expected_author',
        views.collection_add_expected_author,
        name='collection_add_expected_author'
    ),
    path(
        'collection/<slug:slug>/remove_expected_author/<int:profile_id>',
        views.collection_remove_expected_author,
        name='collection_remove_expected_author'
    ),
]
