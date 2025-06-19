__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.core.management import call_command
from django.contrib import admin

from .models import MailAddressDomain, MailLog, MailLogRelation


@admin.action(description="Render and send email")
def send_email(modeladmin, request, queryset):
    for mail_id in queryset.values_list("id", flat=True):
        call_command("send_mails", id=mail_id)


class MailLogRelationInline(admin.TabularInline):
    model = MailLogRelation


@admin.register(MailLog)
class MailLogAdmin(admin.ModelAdmin):
    list_display = ["__str__", "to_recipients", "created", "status", "type"]
    list_filter = ["status", "type"]
    readonly_fields = ["created", "latest_activity"]
    search_fields = [
        "to_recipients",
        "cc_recipients",
        "bcc_recipients",
        "from_email",
        "subject",
        "body",
    ]
    inlines = [MailLogRelationInline]
    actions = [send_email]


@admin.register(MailAddressDomain)
class MailAddressDomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "kind", "organization"]
    list_filter = ["kind"]
    search_fields = ["domain", "organization__name"]
    ordering = ["domain"]
    autocomplete_fields = ["organization"]
