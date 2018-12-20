__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import ConflictOfInterest


class ConflictAdmin(admin.ModelAdmin):
    search_fields = ('header', 'profile__last_name', 'related_profile__last_name')
    list_filter = ('status', 'type')
    list_display = ('header', 'profile', 'related_profile', 'status', 'type')


admin.site.register(ConflictOfInterest, ConflictAdmin)
