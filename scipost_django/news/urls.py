__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("manage/", views.NewsManageView.as_view(), name="manage"),
    path(
        "newscollection/<YYYY:year>-<MM:month>-<DD:day>/",
        views.NewsCollectionView.as_view(),
        name="newscollection_detail",
    ),
    path(
        "newscollection/add/",
        views.NewsCollectionCreateView.as_view(),
        name="newscollection_create",
    ),
    path(
        "newscollection/<int:pk>/update/",
        views.NewsCollectionUpdateView.as_view(),
        name="newscollection_update",
    ),
    path(
        "newscollection/<int:pk>/update_ordering/",
        views.newscollection_update_ordering,
        name="newscollection_update_ordering",
    ),
    path(
        "newscollection/<int:pk>/delete/",
        views.NewsCollectionDeleteView.as_view(),
        name="newscollection_delete",
    ),
    path("newsitem/add/", views.NewsItemCreateView.as_view(), name="newsitem_create"),
    path(
        "newsitem/<int:pk>/",
        views.NewsItemDetailView.as_view(),
        name="newsitem_detail",
    ),
    path(
        "newsitem/<int:pk>/update/",
        views.NewsItemUpdateView.as_view(),
        name="newsitem_update",
    ),
    path(
        "newsitem/<int:pk>/delete/",
        views.NewsItemDeleteView.as_view(),
        name="newsitem_delete",
    ),
    path(
        "add_newsitem_to_newscollection/<int:ncpk>/",
        views.NewsCollectionNewsItemsTableCreateView.as_view(),
        name="add_newsitem_to_newscollection",
    ),
    path("", views.NewsListView.as_view(), name="news"),
]
