__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from conflicts.models import ConflictOfInterest

# from .models import ConflictOfInterest, ConflictGroup
#
#
# class ConflictGroupAdmin(admin.ModelAdmin):
#     search_fields = ['title', 'conflicts__to_name']
#     list_display = ('__str__',)
#
#
# class ConflictOfInterestAdmin(admin.ModelAdmin):
#     search_fields = ['to_contributor__user__last_name', 'to_name']
#     list_filter = ('status', 'type')
#     list_display = ('__str__', 'status', 'type', 'conflict_group')
#
#
admin.site.register(ConflictOfInterest)
# admin.site.register(ConflictOfInterest, ConflictOfInterestAdmin)
