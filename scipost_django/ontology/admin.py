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


@admin.register(AcademicField)
class AcademicFieldAdmin(admin.ModelAdmin):
    search_fields = ["name"]




@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    autocomplete_fields = [
        "topics",
    ]




@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]




@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    autocomplete_fields = [
        "tags",
    ]




@admin.register(RelationAsym)
class RelationAsymAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "A",
        "B",
    ]




@admin.register(RelationSym)
class RelationSymAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "topics",
    ]


