__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^topic/add/$',
        views.TopicCreateView.as_view(),
        name='topic_create'
        ),
    url(
        r'^topic/(?P<slug>[-\w]+)/update/$',
        views.TopicCreateView.as_view(),
        name='topic_update'
        ),
    url(
        r'^topic/(?P<slug>[-\w]+)/$',
        views.TopicDetailView.as_view(),
        name='topic_details'
        ),
    url(
        r'^topics/$',
        views.TopicListView.as_view(),
        name='topics'
        ),
]
