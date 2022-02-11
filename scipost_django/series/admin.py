__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Series, Collection, CollectionPublicationsTable


class SeriesAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]


admin.site.register(Series, SeriesAdmin)


class CollectionPublicationsTableAdmin(admin.StackedInline):
    model = CollectionPublicationsTable
    extra = 0
    autocomplete_fields = [
        "collection",
        "publication",
    ]


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
    ]


admin.site.register(Collection, CollectionAdmin)
