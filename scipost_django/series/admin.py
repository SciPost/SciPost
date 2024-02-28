__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Series, Collection, CollectionPublicationsTable


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]




class CollectionPublicationsTableAdmin(admin.StackedInline):
    model = CollectionPublicationsTable
    extra = 0
    autocomplete_fields = [
        "collection",
        "publication",
    ]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    inlines = [
        CollectionPublicationsTableAdmin,
    ]
    search_fields = [
        "name",
    ]
    autocomplete_fields = [
        "series",
        "submissions",
        "publications",
        "expected_authors",
        "expected_editors",
    ]


