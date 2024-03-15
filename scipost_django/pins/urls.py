__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

app_name = "pins"

from django.urls import path

from . import views

urlpatterns = [
    path(
        "_hx_create/<int:regarding_content_type>/<int:regarding_object_id>",
        views._hx_note_create_form,
        name="hx_note_create_form",
    ),
]
