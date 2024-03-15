__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

app_name = "pins"

from django.urls import include, path

from . import views

urlpatterns = [
    path(
        "<int:regarding_content_type>/<int:regarding_object_id>",
        include(
            [
                path(
                    "_hx_create",
                    views._hx_note_create_form,
                    name="_hx_note_create_form",
                ),
                path(
                    "_hx_list",
                    views._hx_notes_list,
                    name="_hx_notes_list",
                ),
            ]
        ),
    ),
]
