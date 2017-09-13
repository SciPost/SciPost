from django.contrib import admin
from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ('recipient', )
    list_display = ('recipient', 'actor',
                    'level', 'target', 'unread', 'public')
    list_filter = ('level', 'unread', 'public', 'created', )


admin.site.register(Notification, NotificationAdmin)
