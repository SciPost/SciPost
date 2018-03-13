from django.contrib import admin

from .models import MailLog


class MailLogAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'processed']


admin.site.register(MailLog, MailLogAdmin)
