__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'ontology'

urlpatterns = [
    path(
        'acad_field-autocomplete/',
        views.AcademicFieldAutocompleteView.as_view(),
        name='acad_field-autocomplete',
    ),
    path(
        'specialty-autocomplete/',
        views.SpecialtyAutocompleteView.as_view(),
        name='specialty-autocomplete',
    ),
    path(
        'tag-autocomplete/',
        views.TagAutocompleteView.as_view(),
        name='tag-autocomplete',
    ),
    path(
        'topic-autocomplete/',
        views.TopicAutocompleteView.as_view(),
        name='topic-autocomplete',
    ),
    path(
        'topic-linked-autocomplete/',
        views.TopicLinkedAutocompleteView.as_view(),
        name='topic-linked-autocomplete',
    ),
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
        r'^topic/(?P<slug>[-\w]+)/add_tags/$',
        views.topic_add_tags,
        name='topic_add_tags'
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
    url(
        r'^add_relation_asym/(?P<slug>[-\w]+)/$',
        views.add_relation_asym,
        name='add_relation_asym'
    ),
    url(
        r'^delete_relation_asym/(?P<relation_id>[0-9]+)/(?P<slug>[-\w]+)/$',
        views.delete_relation_asym,
        name='delete_relation_asym'
    ),
]
