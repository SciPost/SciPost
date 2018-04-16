__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import MailLog


class MailLogAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'processed']


admin.site.register(MailLog, MailLogAdmin)
