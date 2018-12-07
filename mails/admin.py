__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import MailLog


class MailLogAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'to_recipients', 'created', 'processed']
    readonly_fields = ('created', 'latest_activity')


admin.site.register(MailLog, MailLogAdmin)
