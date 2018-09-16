__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Fellowship, PotentialFellowship, PotentialFellowshipEvent,\
    ProspectiveFellow, ProspectiveFellowEvent


def fellowhip_is_active(fellowship):
    return fellowship.is_active()


class FellowshipAdmin(admin.ModelAdmin):
    search_fields = ['contributor__user__last_name', 'contributor__user__first_name']
    list_display = ('__str__', 'guest', fellowhip_is_active, )
    list_filter = ('guest',)
    fellowhip_is_active.boolean = True
    date_hierarchy = 'created'


admin.site.register(Fellowship, FellowshipAdmin)


class PotentialFellowshipEventInline(admin.TabularInline):
    model = PotentialFellowshipEvent

class PotentialFellowshipAdmin(admin.ModelAdmin):
    inlines = (PotentialFellowshipEventInline,)
    list_display = ('__str__',)
    search_fields = ['last_name', 'email']

admin.site.register(PotentialFellowship, PotentialFellowshipAdmin)


# TO BE DEPRECATED
class ProspectiveFellowEventInline(admin.TabularInline):
    model = ProspectiveFellowEvent

class ProspectiveFellowAdmin(admin.ModelAdmin):
    inlines = (ProspectiveFellowEventInline,)
    search_fields = ['last_name', 'email']

admin.site.register(ProspectiveFellow, ProspectiveFellowAdmin)
