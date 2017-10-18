from django.contrib import admin

from .models import Proceeding


class ProceedingAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'journal', 'open_for_submission',)
    list_filter = ('journal', 'open_for_submission',)


admin.site.register(Proceeding, ProceedingAdmin)
