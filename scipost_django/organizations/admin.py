__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import Organization, OrganizationEvent, ContactPerson, Contact, ContactRole


class OrganizationEventInline(admin.TabularInline):
    model = OrganizationEvent
    extra = 0


class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0


class OrganizationAdmin(GuardedModelAdmin):
    inlines = [
        OrganizationEventInline,
        ContactPersonInline,
    ]
    search_fields = ["name", "acronym"]
    autocomplete_fields = [
        "parent",
        "superseded_by",
    ]


admin.site.register(Organization, OrganizationAdmin)


class ContactRoleInline(admin.TabularInline):
    model = ContactRole
    extra = 0
    autocomplete_fields = [
        "organization",
    ]


class ContactAdmin(admin.ModelAdmin):
    inlines = [
        ContactRoleInline,
    ]
    search_fields = ["user__last_name", "user__first_name", "user__email"]
    autocomplete_fields = [
        "user",
    ]


admin.site.register(Contact, ContactAdmin)


class ContactInline(admin.TabularInline):
    """
    For use as an inline in User admin.
    """

    model = Contact
    extra = 0
