__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.core.management import call_command
from django.contrib import admin

from .models import MailLog, MailLogRelation


def send_email(modeladmin, request, queryset):
    for mail_id in queryset.values_list("id", flat=True):
        call_command("send_mails", id=mail_id)


send_email.short_description = "Render and send email"


class MailLogRelationInline(admin.TabularInline):
    model = MailLogRelation


class MailLogAdmin(admin.ModelAdmin):
    list_display = ["__str__", "to_recipients", "created", "status"]
    list_filter = ["status"]
    readonly_fields = ["created", "latest_activity"]
    search_fields = ["to_recipients", "bcc_recipients", "from_email", "subject", "body"]
    inlines = [MailLogRelationInline]
    actions = [send_email]


admin.site.register(MailLog, MailLogAdmin)
