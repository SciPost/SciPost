__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import *


@admin.register(MailchimpList)
class MailchimpListAdmin(admin.ModelAdmin):
    list_display = ["__str__", "mailchimp_list_id", "status"]
    list_filter = ["status"]

    def has_add_permission(self, *args):
        return False


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    list_display = ["__str__", "is_opt_in", "eligible_count", "subscribed_count"]
    list_filter = ["is_opt_in"]
    autocomplete_fields = ["eligible_subscribers", "subscribed"]

    readonly_fields = ["_email_list"]

    def eligible_count(self, obj):
        return obj.eligible_subscribers.count()

    def subscribed_count(self, obj):
        return obj.subscribed.count()

    def _email_list(self, obj):
        return ", ".join(obj.email_list)
