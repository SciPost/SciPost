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


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    inlines = [
        EmailAccountAccessInline,
    ]




@admin.register(AttachmentFile)
class AttachmentFileAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "uuid",
        "sha224_hash",
    ]




class AttachmentFileInline(admin.StackedInline):
    model = AttachmentFile
    extra = 0
    min_num = 0


class ComposedMessageAPIResponseInline(admin.StackedInline):
    model = ComposedMessageAPIResponse
    extra = 0
    min_num = 0


@admin.register(ComposedMessage)
class ComposedMessageAdmin(admin.ModelAdmin):
    inlines = [
        ComposedMessageAPIResponseInline,
    ]




@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass




@admin.register(StoredMessage)
class StoredMessageAdmin(admin.ModelAdmin):
    pass




@admin.register(UserTag)
class UserTagAdmin(admin.ModelAdmin):
    pass




class AddressValidationInline(admin.StackedInline):
    model = AddressValidation
    extra = 0
    min_num = 0


class AddressBookEntryInline(admin.StackedInline):
    model = AddressBookEntry
    extra = 0
    min_num = 0


@admin.register(ValidatedAddress)
class ValidatedAddressAdmin(admin.ModelAdmin):
    inlines = [
        AddressValidationInline,
        AddressBookEntryInline,
    ]


