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
        "object",
        "admin_link",
        "title",
        "author",
        "created",
    )
    list_filter = (
        "created",
        "modified",
        "visibility",
    )
    search_fields = (
        "title",
        "author__profile__first_name",
        "author__profile__last_name",
    )
    date_hierarchy = "created"
    ordering = ("-created",)
    readonly_fields = ("created", "modified", "object", "admin_link")
    fields = (
        "object",
        "title",
        "description",
        "visibility",
        "author",
        "created",
        "modified",
    )
    autocomplete_fields = ("author",)

    def admin_link(self, obj):
        content_type = obj.regarding_content_type
        admin_url = f"admin:{content_type.app_label}_{content_type.model}_change"
        return format_html(
            '<a href="{url}">[admin]</a>',
            url=reverse(admin_url, args=[obj.regarding_object_id]),
        )

    def object(self, obj):
        content_type = obj.regarding_content_type
        model = content_type.model_class()
        regarding = model.objects.filter(pk=obj.regarding_object_id).first()
        if regarding and hasattr(regarding, "get_absolute_url"):
            return format_html(
                '<a href="{url}">{object}</a>',
                url=regarding.get_absolute_url(),
                object=str(regarding),
            )
        else:
            return f"{content_type} #{obj.regarding_object_id}"
