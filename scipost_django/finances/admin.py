__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    Subsidy,
    SubsidyAttachment,
    WorkLog,
    PeriodicReportType,
    PeriodicReport,
)


class SubsidyAttachmentInline(admin.TabularInline):
    model = SubsidyAttachment


class SubsidyAdmin(admin.ModelAdmin):
    inlines = [
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


admin.site.register(Subsidy, SubsidyAdmin)


class WorkLogAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]


admin.site.register(WorkLog, WorkLogAdmin)


admin.site.register(PeriodicReportType)

admin.site.register(PeriodicReport)
