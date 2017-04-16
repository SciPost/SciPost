from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from submissions.models import *


def submission_short_title(obj):
    return obj.submission.title[:30]


class SubmissionAdmin(GuardedModelAdmin):
    search_fields = ['submitted_by__user__last_name', 'title', 'author_list', 'abstract']
    list_display = ('title', 'author_list', 'status', 'submission_date', 'publication',)
    date_hierarchy = 'submission_date'
    list_filter = ('status', 'discipline', 'submission_type', )


admin.site.register(Submission, SubmissionAdmin)


class EditorialAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list', 'to__user__last_name']
    list_display = ('to', submission_short_title, 'accepted', 'completed', 'date_created',)
    date_hierarchy = 'date_created'
    list_filter = ('accepted', 'deprecated', 'completed', )


admin.site.register(EditorialAssignment, EditorialAssignmentAdmin)


class RefereeInvitationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list',
                     'referee__user__last_name',
                     'first_name', 'last_name', 'email_address']
    list_display = ('referee', submission_short_title, 'accepted', )
    list_filter = ('accepted', 'fulfilled', 'cancelled',)
    date_hierarchy = 'date_invited'


admin.site.register(RefereeInvitation, RefereeInvitationAdmin)


class ReportAdmin(admin.ModelAdmin):
    search_fields = ['author__user__last_name', 'submission']
    list_display = ('author', 'status', submission_short_title, 'date_submitted', )
    list_display_links = ('author',)
    date_hierarchy = 'date_submitted'
    list_filter = ('status',)


admin.site.register(Report, ReportAdmin)


class EditorialCommunicationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'referee__user__last_name', 'text']


admin.site.register(EditorialCommunication, EditorialCommunicationAdmin)


class EICRecommendationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title']


admin.site.register(EICRecommendation, EICRecommendationAdmin)
