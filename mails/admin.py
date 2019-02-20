__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import MailLog, MailLogRelation


class MailLogRelationInline(admin.TabularInline):
    model = MailLogRelation


class MailLogAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'to_recipients', 'created', 'status']
    list_filter = ['status']
    readonly_fields = ('created', 'latest_activity')
    inlines = (MailLogRelationInline,)


admin.site.register(MailLog, MailLogAdmin)
