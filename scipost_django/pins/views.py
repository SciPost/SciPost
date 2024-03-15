__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.contenttypes.models import ContentType
from django.template.response import TemplateResponse

from scipost.permissions import HTMXResponse

from .forms import NoteForm


def _hx_note_create_form(request, regarding_content_type, regarding_object_id):
    regarding_content_type = ContentType.objects.get_for_id(regarding_content_type)
    form = NoteForm(
        request.POST or None,
        initial={
            "author": request.user.contributor,
            "regarding_object_id": regarding_object_id,
            "regarding_content_type": regarding_content_type,
        },
    )
    if form.is_valid():
        form.save()
        response = HTMXResponse("Note created successfully", tag="success")
        response["HX-Trigger"] = "notes-updated"
        return response

    context = {"form": form}

    return TemplateResponse(request, "pins/_hx_note_create_form.html", context)
