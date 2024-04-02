__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from pins.models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "regarding_object_links",
        "title",
        "author",
        "created",
        "modified",
    )
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

    def regarding_object_links(self, obj):
        content_type = obj.regarding_content_type
        model = content_type.model_class()
        regarding = model.objects.get(pk=obj.regarding_object_id)
        admin_url = f"admin:{content_type.app_label}_{content_type.model}_change"
        return format_html(
            "<div style='display: flex; justify-content:space-between;>"
            f'<a href="{regarding.get_absolute_url()}">{regarding}</a>'
            f'<a href="{reverse(admin_url, args=[obj.regarding_object_id])}">[admin]</a>'
            "</div>"
        )
