__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib import admin

from pins.models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id", "regarding__object", "title", "author", "created", "modified")
    list_filter = ("created", "modified", "visibility", "regarding_content_type")
    search_fields = ("title", "author__username")
    date_hierarchy = "created"
    ordering = ("-created",)
    readonly_fields = ("created", "modified", "regarding")
    fields = (
        "title",
        "description",
        "regarding",
        "visibility",
        "author",
        "created",
        "modified",
    )
    autocomplete_fields = ("author",)

    def regarding__object(self, obj):
        return str(obj.regarding)
