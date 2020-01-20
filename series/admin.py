__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Series, Collection, CollectionPublicationsTable


class SeriesAdmin(admin.ModelAdmin):
    pass

admin.site.register(Series, SeriesAdmin)


class CollectionPublicationsTableAdmin(admin.StackedInline):
    model = CollectionPublicationsTable
    extra = 0


class CollectionAdmin(admin.ModelAdmin):
    inlines = [
        CollectionPublicationsTableAdmin,
    ]

admin.site.register(Collection, CollectionAdmin)
