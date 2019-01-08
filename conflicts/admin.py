__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import ConflictOfInterest, ConflictGroup


class ConflictGroupAdmin(admin.ModelAdmin):
    search_fields = ['title', 'conflicts__to_name']
    list_display = ('__str__',)


class ConflictOfInterestAdmin(admin.ModelAdmin):
    search_fields = ['to_contributor__user__last_name', 'to_name']
    list_filter = ('status', 'type')
    list_display = ('__str__', 'status', 'type', 'conflict_group')


admin.site.register(ConflictGroup, ConflictGroupAdmin)
admin.site.register(ConflictOfInterest, ConflictOfInterestAdmin)
