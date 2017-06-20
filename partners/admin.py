from django.contrib import admin

from .models import Contact, Partner, Consortium,\
                    ProspectivePartner, ProspectiveContact, ProspectivePartnerEvent,\
                    MembershipAgreement


class ProspectiveContactInline(admin.TabularInline):
    model = ProspectiveContact
    extra = 0


class ProspectivePartnerEventInline(admin.TabularInline):
    model = ProspectivePartnerEvent


class ProspectivePartnerAdmin(admin.ModelAdmin):
    inlines = (ProspectiveContactInline, ProspectivePartnerEventInline,)
    list_display = ('institution_name', 'date_received', 'status')
    list_filter = ('kind', 'status')


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ('institution', )


class ContactInline(admin.StackedInline):
    model = Contact
    extra = 0
    min_num = 0
    verbose_name = 'Contact (Partners)'


admin.site.register(Partner, PartnerAdmin)
admin.site.register(Consortium)
admin.site.register(ProspectivePartner, ProspectivePartnerAdmin)
admin.site.register(MembershipAgreement)
