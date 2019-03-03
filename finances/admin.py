__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Subsidy, SubsidyAttachment, WorkLog


class SubsidyAttachmentInline(admin.TabularInline):
    model = SubsidyAttachment


class SubsidyAdmin(admin.ModelAdmin):
    inlines = [SubsidyAttachmentInline,]


admin.site.register(Subsidy, SubsidyAdmin)


admin.site.register(WorkLog)
