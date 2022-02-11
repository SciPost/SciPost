__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    AffiliatePublisher,
    AffiliateJournal,
    AffiliatePublication,
    AffiliatePubFraction,
)


admin.site.register(AffiliatePublisher)


class AffiliateJournalAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "publisher"]


admin.site.register(AffiliateJournal, AffiliateJournalAdmin)


class AffiliatePubFractionInline(admin.TabularInline):
    model = AffiliatePubFraction
    list_display = ("organization", "publication", "fraction")
    autocomplete_fields = [
        "organization",
    ]


class AffiliatePublicationAdmin(admin.ModelAdmin):
    search_fields = ["doi", "journal", "publication_date"]
    list_display = ["doi", "journal", "publication_date"]
    inlines = [
        AffiliatePubFractionInline,
    ]


admin.site.register(AffiliatePublication, AffiliatePublicationAdmin)
