__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    Domain,
    EmailAccount, EmailAccountAccess,
    AttachmentFile,
    ComposedMessage, ComposedMessageAPIResponse,
    Event,
    StoredMessage,
    UserTag)


admin.site.register(Domain)


class EmailAccountAccessInline(admin.StackedInline):
    model = EmailAccountAccess
    extra = 0
    min_num = 0


class EmailAccountAdmin(admin.ModelAdmin):
    inlines = [EmailAccountAccessInline,]

admin.site.register(EmailAccount, EmailAccountAdmin)


admin.site.register(AttachmentFile)


class AttachmentFileInline(admin.StackedInline):
    model = AttachmentFile
    extra = 0
    min_num = 0


class ComposedMessageAPIResponseInline(admin.StackedInline):
    model = ComposedMessageAPIResponse
    extra = 0
    min_num = 0


class ComposedMessageAdmin(admin.ModelAdmin):
    inlines = [ComposedMessageAPIResponseInline,]

admin.site.register(ComposedMessage, ComposedMessageAdmin)


class EventAdmin(admin.ModelAdmin):
    pass

admin.site.register(Event, EventAdmin)


class StoredMessageAdmin(admin.ModelAdmin):
    pass

admin.site.register(StoredMessage, StoredMessageAdmin)


class UserTagAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserTag, UserTagAdmin)
