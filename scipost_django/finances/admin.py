__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    Subsidy,
    SubsidyPayment,
    SubsidyAttachment,
    PubFrac,
    WorkLog,
    PeriodicReportType,
    PeriodicReport,
)


class SubsidyPaymentInline(admin.TabularInline):
    model = SubsidyPayment
    autocomplete_fields = [
        "invoice",
        "proof_of_payment",
    ]
    extra = 0

class SubsidyAttachmentInline(admin.TabularInline):
    model = SubsidyAttachment
    extra = 0

@admin.register(Subsidy)
class SubsidyAdmin(admin.ModelAdmin):
    list_display = [
        "organization_name_short",
        "orgtype_display",
        "amount",
        "status",
        "date_from",
        "date_until",
        "total_compensations",
    ]
    list_filter = [
        "organization__orgtype",
    ]
    inlines = [
        SubsidyPaymentInline,
        SubsidyAttachmentInline,
    ]
    autocomplete_fields = [
        "organization",
        "renewal_of",
    ]
    search_fields = [
        "organization__name",
        "organization__name_original",
        "organization__acronym",
    ]

    @admin.display(description="org name short")
    def organization_name_short(self, obj):
        return obj.organization.name[:40]

    @admin.display(description='org type')
    def orgtype_display(self, obj):
        return obj.organization.get_orgtype_display()


@admin.register(SubsidyAttachment)
class SubsidyAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        "kind",
        "date",
        "subsidy",
    ]
    list_filter = [
        "kind",
        "date",
    ]
    autocomplete_fields = [
        "subsidy",
    ]
    search_fields = [
        "description",
        "subsidy__organization__name",
        "subsidy__organization__name_original",
        "subsidy__organization__acronym",
    ]


@admin.register(PubFrac)
class PubFracAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "doi_label_display",
        "fraction",
        "cf_value",
        "compensated_by"
    ]
    autocomplete_fields = [
        "organization",
        "publication",
        "compensated_by",
    ]
    search_fields = [
        "publication__doi_label",
        "organization__name",
        "organization__name_original",
        "organization__acronym",
    ]

    @admin.display(description='doi label')
    def doi_label_display(self, obj):
        return (obj.publication.doi_label)


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]



admin.site.register(PeriodicReportType)

admin.site.register(PeriodicReport)
