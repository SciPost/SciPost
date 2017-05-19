from django.contrib import admin

from .models import ContactPerson, Partner, Consortium,\
    ProspectivePartner, MembershipAgreement


admin.site.register(ContactPerson)


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ['institution', 'institution_acronym',
                     'institution_address', 'contact_person']

admin.site.register(Partner, PartnerAdmin)


admin.site.register(Consortium)


admin.site.register(ProspectivePartner)


admin.site.register(MembershipAgreement)
