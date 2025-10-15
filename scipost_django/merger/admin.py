import json
from django.contrib import admin

from merger.models import NonDuplicateMark, MergeHistoryRecord


@admin.register(NonDuplicateMark)
class NonDuplicateMarkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "object_a",
        "object_b",
        "marked_by",
        "created",
    )
    list_filter = ("content_type",)
    search_fields = (
        "object_a_pk",
        "object_b_pk",
        "description",
    )
    autocomplete_fields = ("marked_by",)
    readonly_fields = ("created",)


@admin.register(MergeHistoryRecord)
class MergeHistoryRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "deprecated_str",
        "kept",
        "performed_by",
        "created",
    )
    list_filter = ("content_type",)
    search_fields = (
        "deprecated_object_pk",
        "kept_object_pk",
        "performed_by",
        "description",
    )
    autocomplete_fields = ("performed_by",)
    readonly_fields = ("created",)

    def deprecated_str(self, obj):
        if obj.deprecated:
            return str(obj.deprecated)
        elif (
            (snapshot := json.loads(obj.deprecated_snapshot))
            and isinstance(snapshot, dict)
            and (snapshot_str := snapshot.get("str"))
        ):
            return f"Deleted (was: {snapshot_str})"
        else:
            return f"Deleted (pk={obj.deprecated_object_pk})"
