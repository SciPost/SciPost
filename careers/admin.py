__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import JobOpening


class JobOpeningAdmin(admin.ModelAdmin):
    pass

admin.site.register(JobOpening, JobOpeningAdmin)
