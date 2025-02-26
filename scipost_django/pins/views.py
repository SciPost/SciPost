__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import HttpResponse
from django.template.response import TemplateResponse

from scipost.permissions import HTMXResponse, permission_required_htmx

from .models import Note
from .forms import NoteForm


@permission_required_htmx("scipost.can_add_notes")
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


def _hx_note_delete(request, pk):
    if request.method != "DELETE":
        return HTMXResponse("Invalid request method", tag="danger")

    note = Note.objects.filter(pk=pk).first()
    if note is None:
        return HTMXResponse("Note not found", tag="danger")

    if note.author == request.user.contributor:
        note.delete()
        return HttpResponse()
    else:
        response = HTMXResponse("You are not the author of this note.", tag="danger")

    response["HX-Trigger"] = "notes-updated"
    return response


def _hx_notes_list(request, regarding_content_type, regarding_object_id):
    regarding_content_type = ContentType.objects.get_for_id(regarding_content_type)
    object = regarding_content_type.get_object_for_this_type(id=regarding_object_id)
    notes = Note.objects.filter(
        regarding_content_type=regarding_content_type,
        regarding_object_id=regarding_object_id,
    )

    # Handle permission checks for viewing and creating notes
    can_create_notes = request.user.has_perm("scipost.can_add_notes")

    # Filter according to the visibility of the notes
    notes = notes.visible_to(request.user, object.__class__)

    context = {
        "object": object,
        "can_create_notes": can_create_notes,
        "notes": notes,
    }
    return TemplateResponse(request, "pins/_hx_notes_list.html", context)
