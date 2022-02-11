__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import (
    AddressBookEntry,
    Domain,
    EmailAccount,
    EmailAccountAccess,
    AttachmentFile,
    ComposedMessage,
    ComposedMessageAPIResponse,
    Event,
    StoredMessage,
    UserTag,
    ValidatedAddress,
    AddressValidation,
)


admin.site.register(Domain)


class EmailAccountAccessInline(admin.StackedInline):
    model = EmailAccountAccess
    extra = 0
    min_num = 0


class EmailAccountAdmin(admin.ModelAdmin):
    inlines = [
        EmailAccountAccessInline,
    ]


admin.site.register(EmailAccount, EmailAccountAdmin)


class AttachmentFileAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "uuid",
        "sha224_hash",
    ]


admin.site.register(AttachmentFile, AttachmentFileAdmin)


class AttachmentFileInline(admin.StackedInline):
    model = AttachmentFile
    extra = 0
    min_num = 0


class ComposedMessageAPIResponseInline(admin.StackedInline):
    model = ComposedMessageAPIResponse
    extra = 0
    min_num = 0


class ComposedMessageAdmin(admin.ModelAdmin):
    inlines = [
        ComposedMessageAPIResponseInline,
    ]


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


class AddressValidationInline(admin.StackedInline):
    model = AddressValidation
    extra = 0
    min_num = 0


class AddressBookEntryInline(admin.StackedInline):
    model = AddressBookEntry
    extra = 0
    min_num = 0


class ValidatedAddressAdmin(admin.ModelAdmin):
    inlines = [
        AddressValidationInline,
        AddressBookEntryInline,
    ]


admin.site.register(ValidatedAddress, ValidatedAddressAdmin)
