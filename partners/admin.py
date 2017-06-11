from django.contrib import admin

from .models import Contact, Partner, PartnerEvent, Consortium,\
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


admin.site.register(Partner, PartnerAdmin)
admin.site.register(Contact)
admin.site.register(Consortium)
admin.site.register(ProspectivePartner, ProspectivePartnerAdmin)
admin.site.register(MembershipAgreement)
