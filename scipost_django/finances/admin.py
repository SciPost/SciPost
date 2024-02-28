__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    Subsidy,
    SubsidyPayment,
    SubsidyAttachment,
    WorkLog,
    PeriodicReportType,
    PeriodicReport,
)


class SubsidyPaymentInline(admin.TabularInline):
    model = SubsidyPayment


class SubsidyAttachmentInline(admin.TabularInline):
    model = SubsidyAttachment


@admin.register(Subsidy)
class SubsidyAdmin(admin.ModelAdmin):
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




@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]




admin.site.register(PeriodicReportType)

admin.site.register(PeriodicReport)
