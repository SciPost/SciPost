__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import MailchimpList


class MailchimpListAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'mailchimp_list_id', 'status']
    list_filter = ['status']

    def has_add_permission(self, *args):
        return False


admin.site.register(MailchimpList, MailchimpListAdmin)
