__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ('recipient', )
    list_display = ('recipient', 'actor',
                    'level', 'target', 'unread',)
    list_filter = ('level', 'unread', 'created',)


admin.site.register(Notification, NotificationAdmin)
