__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Fellowship, PotentialFellowship, PotentialFellowshipEvent


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
    search_fields = ['profile__last_name', 'profile__email']

admin.site.register(PotentialFellowship, PotentialFellowshipAdmin)
