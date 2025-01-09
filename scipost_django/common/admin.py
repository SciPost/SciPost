__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from collections.abc import Sequence
from django.core.handlers.asgi import HttpRequest
from django.utils.html import format_html
from common.models import NonDuplicate
from django.contrib import admin


@admin.register(NonDuplicate)
class NonDuplicateAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "_model",
        "object_a",
        "object_b",
        "description",
        "created",
    ]
    search_fields = ["description"]
    autocomplete_fields = ["contributor"]
    list_filter = ["content_type"]
    date_hierarchy = "created"

    def _model(self, obj):
        return str(obj.content_type.model).title()

    def object_a(self, obj):
        return format_html(
            "<a href='{url}'>{id}</a> {str}".format(
                url=obj.object_a.get_absolute_url(),
                id=obj.object_a.id,
                str=str(obj.object_a),
            )
        )

    def object_b(self, obj):
        return format_html(
            "<a href='{url}'>{id}</a> {str}".format(
                url=obj.object_b.get_absolute_url(),
                id=obj.object_b.id,
                str=str(obj.object_b),
            )
        )
