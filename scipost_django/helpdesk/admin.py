__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import Queue, Ticket, Followup


class QueueAdmin(GuardedModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']

admin.site.register(Queue, QueueAdmin)


class FollowupInline(admin.TabularInline):
    model = Followup
    extra = 0
    autocomplete_fields = [
        'by',
    ]


class TicketAdmin(admin.ModelAdmin):
    search_fields = [
        'title',
        'description',
        'defined_by__last_name',
        'concerning_object_id'
    ]
    inlines = [FollowupInline]
    autocomplete_fields = [
        'defined_by',
        'assigned_to',
    ]

admin.site.register(Ticket, TicketAdmin)
