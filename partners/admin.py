__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Organization, Contact, Partner, Consortium, Institution,\
                    ProspectivePartner, ProspectiveContact, ProspectivePartnerEvent,\
                    MembershipAgreement, ContactRequest, PartnersAttachment


class OrganizationAdmin(admin.ModelAdmin):
    search_fields = ['name', 'acronym']


class AttachmentInline(admin.TabularInline):
    model = PartnersAttachment


class ContactToPartnerInline(admin.TabularInline):
    model = Contact.partners.through
    extra = 0
    verbose_name = 'Contact'
    verbose_name_plural = 'Contacts'


class ContactToUserInline(admin.StackedInline):
    model = Contact
    extra = 0
    min_num = 0
    verbose_name = 'Contact (Partners)'


class ProspectiveContactInline(admin.TabularInline):
    model = ProspectiveContact
    extra = 0


class ProspectivePartnerEventInline(admin.TabularInline):
    model = ProspectivePartnerEvent
    extra = 0


class ProspectivePartnerAdmin(admin.ModelAdmin):
    inlines = (ProspectiveContactInline, ProspectivePartnerEventInline,)
    list_display = ('institution_name', 'date_received', 'date_processed', 'status')
    list_filter = ('kind', 'status')


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ('institution', )
    inlines = (
        ContactToPartnerInline,
    )


class MembershipAgreementAdmin(admin.ModelAdmin):
    inlines = (
        AttachmentInline,
    )


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(Consortium)
admin.site.register(Contact)
admin.site.register(ContactRequest)
admin.site.register(Institution)
admin.site.register(ProspectivePartner, ProspectivePartnerAdmin)
admin.site.register(MembershipAgreement, MembershipAgreementAdmin)
