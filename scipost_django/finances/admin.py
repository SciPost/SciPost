__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from finances.models.account import Account
from finances.models.balance import Balance
from finances.models.transaction import FuturePeriodicTransaction

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

    @admin.display(description="org type")
    def orgtype_display(self, obj):
        return obj.organization.get_orgtype_display()


@admin.action(description="Detach from all schedules")
def detach(modeladmin, request, queryset):
    for obj in queryset:
        if (payment_proof := getattr(obj, "proof_of_payment_for", None)) is not None:
            payment_proof.proof_of_payment = None
            payment_proof.save()
        if (invoice_proof := getattr(obj, "invoice_for", None)) is not None:
            invoice_proof.invoice = None
            invoice_proof.save()


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
    actions = [detach]


@admin.register(SubsidyPayment)
class SubsidyPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "subsidy",
        "reference",
        "amount",
        "date_scheduled",
        "status",
    ]
    autocomplete_fields = [
        "subsidy",
        "invoice",
        "proof_of_payment",
    ]
    search_fields = [
        "reference",
        "amount",
        "subsidy__organization__name",
        "subsidy__organization__name_original",
        "subsidy__organization__acronym",
    ]

    def status(self, obj):
        return obj.status


@admin.register(PubFrac)
class PubFracAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "doi_label_display",
        "fraction",
        "cf_value",
        "compensated_by",
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

    @admin.display(description="doi label")
    def doi_label_display(self, obj):
        return obj.publication.doi_label


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]


admin.site.register(PeriodicReportType)

admin.site.register(PeriodicReport)


class BalanceInline(admin.TabularInline):
    model = Balance
    extra = 0


class FuturePeriodicTransactionInline(admin.TabularInline):
    model = FuturePeriodicTransaction
    extra = 0


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "description"]
    search_fields = ["number", "name"]
    inlines = [
        FuturePeriodicTransactionInline,
        BalanceInline,
    ]
