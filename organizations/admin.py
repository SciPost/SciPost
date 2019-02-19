__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Organization, OrganizationEvent, ContactPerson, Contact, ContactRole


class OrganizationEventInline(admin.TabularInline):
    model = OrganizationEvent
    extra = 0

class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0

class OrganizationAdmin(admin.ModelAdmin):
    inlines = [OrganizationEventInline, ContactPersonInline,]
    search_fields = ['name', 'acronym']


admin.site.register(Organization, OrganizationAdmin)


class ContactRoleInline(admin.TabularInline):
    model = ContactRole
    extra = 0

class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactRoleInline,]
    search_fields = ['user__last_name', 'user__first_name', 'user__email']


admin.site.register(Contact, ContactAdmin)
