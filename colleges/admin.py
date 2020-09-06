__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import College, Fellowship, PotentialFellowship, PotentialFellowshipEvent


admin.site.register(College)


def fellowhip_is_active(fellowship):
    return fellowship.is_active()


class FellowshipAdmin(admin.ModelAdmin):
    search_fields = ['contributor__user__last_name', 'contributor__user__first_name']
    list_display = ('__str__', 'college', 'guest', fellowhip_is_active, )
    list_filter = ('guest',)
    fellowhip_is_active.boolean = True
    date_hierarchy = 'created'
    autocomplete_fields = [
        'contributor',
    ]


admin.site.register(Fellowship, FellowshipAdmin)


class PotentialFellowshipEventInline(admin.TabularInline):
    model = PotentialFellowshipEvent
    autocomplete_fields = [
        'potfel',
        'noted_by',
    ]


class PotentialFellowshipAdmin(admin.ModelAdmin):
    inlines = [
        PotentialFellowshipEventInline,
    ]
    list_display = [
        '__str__',
    ]
    search_fields = [
        'profile__last_name',
        'profile__first_name'
    ]
    autocomplete_fields = [
        'profile',
        'in_agreement',
        'in_abstain',
        'in_disagreement',
    ]

admin.site.register(PotentialFellowship, PotentialFellowshipAdmin)
