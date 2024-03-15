__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.contenttypes.models import ContentType
from django.template.response import TemplateResponse

from scipost.permissions import HTMXResponse

from .models import Note
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


def _hx_notes_list(request, regarding_content_type, regarding_object_id):
    regarding_content_type = ContentType.objects.get_for_id(regarding_content_type)
    object = regarding_content_type.get_object_for_this_type(id=regarding_object_id)
    notes = Note.objects.filter(
        regarding_content_type=regarding_content_type,
        regarding_object_id=regarding_object_id,
    )

    # TODO: Filter to the notes that the user has permission to see
    # ...

    context = {
        "object": object,
        "notes": notes,
    }
    return TemplateResponse(request, "pins/_hx_notes_list.html", context)
