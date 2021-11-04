__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    path(
        'manage/',
        views.NewsManageView.as_view(),
        name='manage'
    ),
    path(
        'newsletter/<YYYY:year>-<MM:month>-<DD:day>/',
        views.NewsLetterView.as_view(),
        name='newsletter_detail'
    ),
    path(
        'newsletter/add/',
        views.NewsLetterCreateView.as_view(),
        name='newsletter_create'
    ),
    path(
        'newsletter/<int:pk>/update/',
        views.NewsLetterUpdateView.as_view(),
        name='newsletter_update'
    ),
    path(
        'newsletter/<int:pk>/update_ordering/',
        views.newsletter_update_ordering,
        name='newsletter_update_ordering'
    ),
    path(
        'newsletter/<int:pk>/delete/',
        views.NewsLetterDeleteView.as_view(),
        name='newsletter_delete'
    ),
    path(
        'newsitem/add/',
        views.NewsItemCreateView.as_view(),
        name='newsitem_create'
    ),
    path(
        'newsitem/<int:pk>/update/',
        views.NewsItemUpdateView.as_view(),
        name='newsitem_update'
    ),
    path(
        'newsitem/<int:pk>/delete/',
        views.NewsItemDeleteView.as_view(),
        name='newsitem_delete'
    ),
    path(
        'add_newsitem_to_newsletter/<int:nlpk>/',
        views.NewsLetterNewsItemsTableCreateView.as_view(),
        name='add_newsitem_to_newsletter'
    ),
    path(
        '', views.NewsListView.as_view(), name='news'
    ),
]
