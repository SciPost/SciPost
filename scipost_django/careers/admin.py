__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin

from .models import JobOpening, JobApplication, WorkContract


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    pass


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    fields = [
        "status",
        "job_opening",
        "date_received",
        "title",
        "first_name",
        "last_name",
        "email",
        "motivation",
        "cv",
    ]


@admin.register(WorkContract)
class WorkContractAdmin(admin.ModelAdmin):
    exclude = []
    list_display = [
        "__str__",
        "salary_type",
        "pay_rate",
        "fte",
        "start_date",
        "end_date",
    ]
    autocomplete_fields = ["employee"]
    list_filter = ["salary_type"]
