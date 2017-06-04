from django.contrib import admin

from .models import Contact, Partner, Consortium,\
    ProspectivePartner, MembershipAgreement


admin.site.register(Contact)


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ['institution', ]


admin.site.register(Partner, PartnerAdmin)
admin.site.register(Consortium)
admin.site.register(ProspectivePartner)
admin.site.register(MembershipAgreement)
