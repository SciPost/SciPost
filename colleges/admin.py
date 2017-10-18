from django.contrib import admin

from .models import Fellowship


def fellowhip_is_active(fellowship):
    return fellowship.is_active()


class FellowshipAdmin(admin.ModelAdmin):
    search_fields = ['contributor__last_name', 'contributor__first_name']
    list_display = ('__str__', 'guest', fellowhip_is_active, )
    list_filter = ('guest',)
    fellowhip_is_active.boolean = True
    date_hierarchy = 'created'


admin.site.register(Fellowship, FellowshipAdmin)
