from django.contrib import admin, messages

from .models import ActiveMailchimpList


class ActiveMailchimpListAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'mailchimp_list_id', 'status']
    list_filter = ['status']
    actions = ['update_lists']

    def message_user(self, request, *args):
        return messages.warning(request, 'Sorry, Deposit\'s are readonly.')

    def has_add_permission(self, *args):
        return False

    def update_lists(self, request, queryset):
        messages.success(request, 'Test')

    # def has_delete_permission(self, *args):
    #     return False

admin.site.register(ActiveMailchimpList, ActiveMailchimpListAdmin)
