__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import ConflictOfInterest


class ConflictAdmin(admin.ModelAdmin):
    search_fields = (
        'header',
        'profile__last_name',
        'related_profile__last_name',
        'related_submissions__title',
        'related_submissions__preprint__identifier_w_vn_nr'
    )
    list_filter = ('status', 'type')
    list_display = ('header', 'profile', 'related_profile', 'status', 'type')


admin.site.register(ConflictOfInterest, ConflictAdmin)
