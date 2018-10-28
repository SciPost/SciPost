__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.ontology,
        name='ontology'
    ),
    url(
        r'^topic/add/$',
        views.TopicCreateView.as_view(),
        name='topic_create'
    ),
    url(
        r'^topic/(?P<slug>[-\w]+)/add_tag/$',
        views.topic_add_tag,
        name='topic_add_tag'
    ),
    url(
        r'^topic/(?P<slug>[-\w]+)/remove_tag/(?P<tag_id>[0-9]+)/$',
        views.topic_remove_tag,
        name='topic_remove_tag'
    ),
    url(
        r'^topic/(?P<slug>[-\w]+)/update/$',
        views.TopicUpdateView.as_view(),
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
