__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "ontology"

urlpatterns = [
    path(
        "acad_field-autocomplete/",
        views.AcademicFieldAutocompleteView.as_view(),
        name="acad_field-autocomplete",
    ),
    path(
        "specialty-autocomplete/",
        views.SpecialtyAutocompleteView.as_view(),
        name="specialty-autocomplete",
    ),
    path(
        "tag-autocomplete/",
        views.TagAutocompleteView.as_view(),
        name="tag-autocomplete",
    ),
    path(
        "topic-autocomplete/",
        views.TopicAutocompleteView.as_view(),
        name="topic-autocomplete",
    ),
    path(
        "topic-linked-autocomplete/",
        views.TopicLinkedAutocompleteView.as_view(),
        name="topic-linked-autocomplete",
    ),
    path(
        "_hx_topic_dynsel_list",
        views._hx_topic_dynsel_list,
        name="_hx_topic_dynsel_list",
    ),
    path(
        "set_session_acad_field",
        views.set_session_acad_field,
        name="set_session_acad_field",
    ),
    path(
        "_hx_session_specialty_form",
        views._hx_session_specialty_form,
        name="_hx_session_specialty_form",
    ),
    path(
        "set_session_specialty",
        views.set_session_specialty,
        name="set_session_specialty",
    ),
    path("", views.ontology, name="ontology"),
    path("topic/add/", views.TopicCreateView.as_view(), name="topic_create"),
    path("topic/<slug:slug>/add_tags/", views.topic_add_tags, name="topic_add_tags"),
    path(
        "topic/<slug:slug>/remove_tag/<int:tag_id>/",
        views.topic_remove_tag,
        name="topic_remove_tag",
    ),
    path(
        "topic/<slug:slug>/update/",
        views.TopicUpdateView.as_view(),
        name="topic_update",
    ),
    path("topic/<slug:slug>/", views.TopicDetailView.as_view(), name="topic_details"),
    path("topics/", views.TopicListView.as_view(), name="topics"),
    path(
        "add_relation_asym/<slug:slug>/",
        views.add_relation_asym,
        name="add_relation_asym",
    ),
    path(
        "delete_relation_asym/<int:relation_id>/<slug:slug>/",
        views.delete_relation_asym,
        name="delete_relation_asym",
    ),
]
