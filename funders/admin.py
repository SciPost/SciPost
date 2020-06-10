__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Funder, Grant


admin.site.register(Funder)



class GrantAdmin(admin.ModelAdmin):
    search_fields = [
        'funder__name',
        'number',
        'recipient_name',
        'recipiend__user__last_name',
    ]
    autocomplete_fields = [
        'funder',
        'recipient',
    ]

admin.site.register(Grant, GrantAdmin)
