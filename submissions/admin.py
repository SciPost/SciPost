from django.contrib import admin

from submissions.models import *


class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ['submitted_by__user__username', 'title', 'abstract']

admin.site.register(Submission, SubmissionAdmin)


class ReportAdmin(admin.ModelAdmin):
    search_fields = ['author__user__username']

admin.site.register(Report, ReportAdmin)
