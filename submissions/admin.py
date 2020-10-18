__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django.db.models import Q
from django import forms

from guardian.admin import GuardedModelAdmin

from submissions.models import (
    Submission, EditorialAssignment, RefereeInvitation, Report, EditorialCommunication,
    EICRecommendation, SubmissionTiering, AlternativeRecommendation, EditorialDecision,
    SubmissionEvent, iThenticateReport, PreprintServer)
from scipost.models import Contributor
from colleges.models import Fellowship


def submission_short_title(obj):
    return obj.submission.title[:30]


class PreprintServerAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'acad_fields'
    ]

admin.site.register(PreprintServer, PreprintServerAdmin)


class iThenticateReportAdmin(admin.ModelAdmin):
    list_display = ['doc_id', 'to_submission', 'status']
    list_filter = ['status']
    search_fields = [
        'doc_id',
    ]

admin.site.register(iThenticateReport, iThenticateReportAdmin)


class SubmissionTieringInline(admin.StackedInline):
    model = SubmissionTiering
    extra = 0
    min_num = 0
    autocomplete_fields = [
        'submission',
        'fellow',
        'for_journal',
    ]


class SubmissionAdmin(GuardedModelAdmin):
    date_hierarchy = 'submission_date'
    list_display = (
        'title',
        'author_list',
        'preprint',
        'submitted_to',
        'status',
        'visible_public',
        'visible_pool',
        'refereeing_cycle',
        'submission_date',
        'publication'
    )
    list_filter = (
        'status',
        'acad_field',
        'specialties',
        'submitted_to'
    )
    search_fields = [
        'submitted_by__user__last_name',
        'title',
        'author_list',
        'abstract',
    ]
    autocomplete_fields = [
        'acad_field',
        'specialties',
        'preprint',
        'editor_in_charge',
        'is_resubmission_of',
        'fellows',
        'submitted_by',
        'voting_fellows',
        'submitted_to',
        'proceedings',
        'authors',
        'authors_claims',
        'authors_false_claims',
        'plagiarism_report',
        'topics',
    ]
    readonly_fields = ('publication',)
    inlines = [
        SubmissionTieringInline,
    ]

    # Admin fields should be added in the fieldsets
    radio_fields = {
        "acad_field": admin.VERTICAL,
        "submitted_to": admin.VERTICAL,
        "refereeing_cycle": admin.HORIZONTAL
    }
    fieldsets = (
        (None, {
            'fields': (
                'preprint',
                'publication',
                'title',
                'abstract'),
        }),
        ('Versioning', {
            'fields': (
                'thread_hash',
                'is_current',
                'is_resubmission_of',
                'list_of_changes'),
        }),
        ('Submission details', {
            'classes': ('collapse',),
            'fields': (
                'code_repository_url',
                'data_repository_url',
                'author_comments',
                'acad_field',
                'specialties',
                'approaches',
                'proceedings'),
        }),
        ('Authors', {
            'classes': ('collapse',),
            'fields': (
                'submitted_by',
                'author_list',
                'authors',
                'authors_claims',
                'authors_false_claims'),
        }),
        ('Refereeing', {
            'classes': ('collapse',),
            'fields': (
                'editor_in_charge',
                'status',
                ('visible_public', 'visible_pool'),
                'refereeing_cycle',
                ('open_for_commenting', 'open_for_reporting'),
                'reporting_deadline',
                'acceptance_date',
                'referees_flagged',
                'referees_suggested',
                'remarks_for_editors',
                'submitted_to',
                'pdf_refereeing_pack',
                'plagiarism_report',
                'fellows',
                'voting_fellows'),
        }),
        ('Meta', {
            'classes': ('collapse',),
            'fields': (
                'metadata',
                'submission_date',
                'needs_conflicts_update'
            ),
        }),
    )

admin.site.register(Submission, SubmissionAdmin)


class EditorialAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list', 'to__user__last_name']
    list_display = (
        'to', submission_short_title, 'status', 'date_created', 'date_invited', 'invitation_order')
    date_hierarchy = 'date_created'
    list_filter = ('status',)
    autocomplete_fields = [
        'submission',
        'to',
    ]

admin.site.register(EditorialAssignment, EditorialAssignmentAdmin)


class RefereeInvitationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list',
                     'referee__user__last_name',
                     'first_name', 'last_name', 'email_address']
    list_display = ('__str__', 'accepted', )
    list_filter = ('accepted', 'fulfilled', 'cancelled',)
    date_hierarchy = 'date_invited'
    autocomplete_fields = [
        'profile',
        'submission',
        'referee',
        'invited_by',
    ]

admin.site.register(RefereeInvitation, RefereeInvitationAdmin)


class ReportAdmin(admin.ModelAdmin):
    search_fields = ['author__user__last_name', 'submission__title']
    list_display = ('author', 'status', 'doi_label', submission_short_title, 'date_submitted', )
    list_display_links = ('author',)
    date_hierarchy = 'date_submitted'
    list_filter = ('status',)
    readonly_fields = ('report_nr',)
    autocomplete_fields = [
        'submission',
        'vetted_by',
        'author',
    ]

admin.site.register(Report, ReportAdmin)


class EditorialCommunicationAdmin(admin.ModelAdmin):
    search_fields = [
        'submission__title',
        'referee__user__last_name',
        'text'
    ]
    autocomplete_fields = [
        'submission',
        'referee'
    ]

admin.site.register(EditorialCommunication, EditorialCommunicationAdmin)


class AlternativeRecommendationInline(admin.StackedInline):
    model = AlternativeRecommendation
    extra = 0
    min_num = 0
    autocomplete_fields = [
        'fellow',
        'for_journal',
    ]


class EICRecommendationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title']
    list_filter = ('status',)
    list_display = (submission_short_title, 'for_journal', 'recommendation',
                    'status', 'active', 'version')
    inlines = [
        AlternativeRecommendationInline,
    ]
    autocomplete_fields = [
        'submission',
        'eligible_to_vote',
        'voted_for',
        'voted_against',
        'voted_abstain',
    ]

admin.site.register(EICRecommendation, EICRecommendationAdmin)


class EditorialDecisionAdmin(admin.ModelAdmin):
    search_fields = [
        'submission__title',
        'submission__author_list',
        'submission__preprint__identifier_w_vn_nr'
    ]
    list_filter = ['for_journal', 'decision', 'status',]
    list_display = [submission_short_title, 'for_journal', 'decision',
                    'taken_on', 'status', 'version']
    autocomplete_fields = [
        'submission',
        'for_journal',
    ]

admin.site.register(EditorialDecision, EditorialDecisionAdmin)


class SubmissionEventAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'submission',
    ]

admin.site.register(SubmissionEvent, SubmissionEventAdmin)
