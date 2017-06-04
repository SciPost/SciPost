from django.contrib import admin

from .models import Contact, Partner, Consortium, ProspectivePartner, MembershipAgreement,\
                    ProspectiveContact


class ProspectiveContactInline(admin.TabularInline):
    model = ProspectiveContact
    extra = 0


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ('institution', )


class ProspectivePartnerAdmin(admin.ModelAdmin):
    inlines = (ProspectiveContactInline,)
    list_display = ('institution_name', 'date_received', 'status')
    list_filter = ('kind', 'status')


admin.site.register(Partner, PartnerAdmin)
admin.site.register(Contact)
admin.site.register(Consortium)
admin.site.register(ProspectivePartner, ProspectivePartnerAdmin)
admin.site.register(MembershipAgreement)
