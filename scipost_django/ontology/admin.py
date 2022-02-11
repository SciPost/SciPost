__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    Branch,
    AcademicField,
    Specialty,
    Tag,
    Topic,
    RelationAsym,
    RelationSym,
)


admin.site.register(Branch)


class AcademicFieldAdmin(admin.ModelAdmin):
    search_fields = ["name"]


admin.site.register(AcademicField, AcademicFieldAdmin)


class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ["name"]


admin.site.register(Specialty, SpecialtyAdmin)


class TagAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]


admin.site.register(Tag, TagAdmin)


class TopicAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    autocomplete_fields = [
        "tags",
    ]


admin.site.register(Topic, TopicAdmin)


class RelationAsymAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "A",
        "B",
    ]


admin.site.register(RelationAsym, RelationAsymAdmin)


class RelationSymAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "topics",
    ]


admin.site.register(RelationSym, RelationSymAdmin)
