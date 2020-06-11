__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    autocomplete_fields = ('recipient', )
    list_display = ('recipient', 'actor',
                    'level', 'target', 'unread',)
    list_filter = ('level', 'unread', 'created',)
    search_fields = ['recipient__last_name', 'verb', 'description']

admin.site.register(Notification, NotificationAdmin)
