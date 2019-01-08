__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import Proceedings


class ProceedingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'issue',)
    list_filter = ('issue',)


admin.site.register(Proceedings, ProceedingsAdmin)
