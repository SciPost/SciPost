__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Event, StoredMessage, StoredMessageAttachment


class EventAdmin(admin.ModelAdmin):
    pass

admin.site.register(Event, EventAdmin)


class StoredMessageAttachmentInline(admin.StackedInline):
    model = StoredMessageAttachment
    extra = 0
    min_num = 0


class StoredMessageAdmin(admin.ModelAdmin):
    inlines = [StoredMessageAttachmentInline,]

admin.site.register(StoredMessage, StoredMessageAdmin)
