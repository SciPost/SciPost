__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'news'

urlpatterns = [
    url(r'^manage/$',
        views.NewsManageView.as_view(),
        name='manage'),
    url(r'^newsletter/(?P<year>[0-9]{4,})-(?P<month>[0-9]{2,})-(?P<day>[0-9]{2,})/$',
        views.NewsLetterView.as_view(),
        name='newsletter_detail'),
    url(r'^newsletter/add/$',
        views.NewsLetterCreateView.as_view(),
        name='newsletter_create'),
    url(r'^newsletter/(?P<pk>[0-9]+)/update/$',
        views.NewsLetterUpdateView.as_view(),
        name='newsletter_update'),
    url(r'^newsletter/(?P<pk>[0-9]+)/update_ordering/$',
        #views.NewsLetterNewsItemsOrderingUpdateView.as_view(),
        views.newsletter_update_ordering,
        name='newsletter_update_ordering'),
    url(r'^newsletter/(?P<pk>[0-9]+)/delete/$',
        views.NewsLetterDeleteView.as_view(),
        name='newsletter_delete'),
    url(r'^newsitem/add/$',
        views.NewsItemCreateView.as_view(),
        name='newsitem_create'),
    url(r'^newsitem/(?P<pk>[0-9]+)/update/$',
        views.NewsItemUpdateView.as_view(),
        name='newsitem_update'),
    url(r'^newsitem/(?P<pk>[0-9]+)/delete/$',
        views.NewsItemDeleteView.as_view(),
        name='newsitem_delete'),
    url(r'^add_newsitem_to_newsletter/(?P<nlpk>[0-9]+)/$',
        views.NewsLetterNewsItemsTableCreateView.as_view(),
        name='add_newsitem_to_newsletter'),
    url(r'^$', views.NewsListView.as_view(), name='news'),
]
