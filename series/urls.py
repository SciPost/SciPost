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
]
