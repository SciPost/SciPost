__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import JobOpening, JobApplication


class JobOpeningAdmin(admin.ModelAdmin):
    pass


admin.site.register(JobOpening, JobOpeningAdmin)


class JobApplicationAdmin(admin.ModelAdmin):
    fields = [
        "status",
        "jobopening",
        "date_received",
        "title",
        "first_name",
        "last_name",
        "email",
        "motivation",
        "cv",
    ]


admin.site.register(JobApplication, JobApplicationAdmin)
