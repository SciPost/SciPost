from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from submissions.models import *


class SubmissionAdmin(GuardedModelAdmin):
    search_fields = ['submitted_by__user__last_name', 'title', 'author_list', 'abstract']

admin.site.register(Submission, SubmissionAdmin)


class EditorialAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list', 'to__user__last_name']

admin.site.register(EditorialAssignment, EditorialAssignmentAdmin)


class RefereeInvitationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list',
                     'referee__user__last_name',
                     'first_name', 'last_name', 'email_address', ]
                     

admin.site.register(RefereeInvitation, RefereeInvitationAdmin)


class ReportAdmin(admin.ModelAdmin):
    search_fields = ['author__user__last_name']

admin.site.register(Report, ReportAdmin)


class EditorialCommunicationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'referee__user__last_name', 'text']

admin.site.register(EditorialCommunication, EditorialCommunicationAdmin)


class EICRecommendationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title']

admin.site.register(EICRecommendation, EICRecommendationAdmin)
