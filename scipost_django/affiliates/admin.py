__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    AffiliatePublisher,
    AffiliateJournal,
    AffiliatePublication,
    AffiliatePubFraction,
    AffiliateJournalYearSubsidy,
)


admin.site.register(AffiliatePublisher)


class AffiliateJournalAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "publisher"]


admin.site.register(AffiliateJournal, AffiliateJournalAdmin)


class AffiliateJournalYearSubsidyAdmin(admin.ModelAdmin):
    search_fields = ["journal", "organization", "year"]
    list_display =["journal", "year", "amount", "organization"]

admin.site.register(AffiliateJournalYearSubsidy, AffiliateJournalYearSubsidyAdmin)


class AffiliatePubFractionInline(admin.TabularInline):
    model = AffiliatePubFraction
    list_display = ("organization", "publication", "fraction")
    autocomplete_fields = [
        "organization",
    ]


class AffiliatePublicationAdmin(admin.ModelAdmin):
    search_fields = ["doi", "journal__name", "publication_date"]
    list_display = ["doi", "journal", "publication_date"]
    inlines = [
        AffiliatePubFractionInline,
    ]


admin.site.register(AffiliatePublication, AffiliatePublicationAdmin)
