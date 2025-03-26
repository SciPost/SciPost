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
        "web_link",
        "admin_link",
        "title",
        "author",
        "created",
        "modified",
    )
    list_filter = ("created", "modified", "visibility")
    search_fields = (
        "title",
        "author__profile__first_name",
        "author__profile__last_name",
    )
    date_hierarchy = "created"
    ordering = ("-created",)
    readonly_fields = ("created", "modified", "web_link", "admin_link")
    fields = (
        "web_link",
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
            '<a href="{}">[admin]</a>',
            reverse(admin_url, args=[obj.regarding_object_id]),
        )

    def web_link(self, obj):
        content_type = obj.regarding_content_type
        model = content_type.model_class()
        regarding = model.objects.get(pk=obj.regarding_object_id)
        return format_html(f'<a href="{regarding.get_absolute_url()}">{regarding}</a>')
