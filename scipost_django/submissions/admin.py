__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django.db.models import Q
from django import forms

from guardian.admin import GuardedModelAdmin
from ethics.admin import RedFlagInline

from submissions.models import (
    SubmissionAuthorProfile,
    Submission,
    EditorialAssignment,
    RefereeInvitation,
    Report,
    EditorialCommunication,
    EICRecommendation,
    SubmissionTiering,
    AlternativeRecommendation,
    EditorialDecision,
    SubmissionEvent,
    iThenticateReport,
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
    Qualification,
    Readiness,
    PreprintServer,
    RefereeIndication,
)
from scipost.models import Contributor
from colleges.models import Fellowship
from ethics.models import SubmissionClearance


def submission_short_title(obj):
    return obj.submission.title[:30]


def submission_short_authors(obj):
    return obj.submission.author_list[:20]


@admin.register(PreprintServer)
class PreprintServerAdmin(admin.ModelAdmin):
    autocomplete_fields = ["acad_fields"]


@admin.register(iThenticateReport)
class iThenticateReportAdmin(admin.ModelAdmin):
    list_display = ["doc_id", "to_submission", "status"]
    list_filter = ["status"]
    search_fields = [
        "doc_id",
    ]


class InternalPlagiarismAssessmentInline(admin.StackedInline):
    model = InternalPlagiarismAssessment


class iThenticatePlagiarismAssessmentInline(admin.StackedInline):
    model = iThenticatePlagiarismAssessment


class QualificationInline(admin.StackedInline):
    model = Qualification
    extra = 0
    min_num = 0
    autocomplete_fields = [
        "submission",
        "fellow",
    ]


class ReadinessInline(admin.StackedInline):
    model = Readiness
    extra = 0
    min_num = 0
    autocomplete_fields = [
        "submission",
        "fellow",
    ]


class SubmissionClearanceInline(admin.StackedInline):
    model = SubmissionClearance
    extra = 0
    min_num = 0
    autocomplete_fields = [
        "profile",
        "submission",
        "asserted_by",
    ]


class SubmissionAuthorProfileInline(admin.TabularInline):
    model = SubmissionAuthorProfile
    extra = 0
    autocomplete_fields = [
        "profile",
        "affiliations",
    ]


class SubmissionTieringInline(admin.StackedInline):
    model = SubmissionTiering
    extra = 0
    min_num = 0
    autocomplete_fields = [
        "submission",
        "fellow",
        "for_journal",
    ]


class CollectionInline(admin.StackedInline):
    model = Submission.collections.through
    extra = 0
    autocomplete_fields = [
        "collection",
    ]


@admin.register(Submission)
class SubmissionAdmin(GuardedModelAdmin):
    date_hierarchy = "submission_date"
    list_display = (
        "title",
        "author_list",
        "preprint",
        "submitted_to",
        "status",
        "visible_public",
        "visible_pool",
        "refereeing_cycle",
        "submission_date",
    )
    list_filter = ("status", "acad_field", "specialties", "submitted_to")
    search_fields = [
        "submitted_by__user__last_name",
        "title",
        "author_list",
        "abstract",
        "preprint__identifier_w_vn_nr",
    ]
    autocomplete_fields = [
        "acad_field",
        "specialties",
        "preprint",
        "editor_in_charge",
        "followup_of",
        "is_resubmission_of",
        "fellows",
        "submitted_by",
        "submitted_to",
        "proceedings",
        "authors",
        "authors_claims",
        "authors_false_claims",
        "iThenticate_plagiarism_report",
        "topics",
    ]
    inlines = [
        InternalPlagiarismAssessmentInline,
        iThenticatePlagiarismAssessmentInline,
        SubmissionAuthorProfileInline,
        QualificationInline,
        ReadinessInline,
        SubmissionClearanceInline,
        SubmissionTieringInline,
        CollectionInline,
        RedFlagInline,
    ]

    # Admin fields should be added in the fieldsets
    radio_fields = {
        "acad_field": admin.VERTICAL,
        "submitted_to": admin.VERTICAL,
        "refereeing_cycle": admin.HORIZONTAL,
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "preprint",
                    "title",
                    "abstract",
                    "author_list",
                    "submission_date",
                    "submitted_to",
                    "status",
                ),
            },
        ),
        (
            "Submission details",
            {
                "classes": ("collapse",),
                "fields": (
                    "fulfilled_expectations",
                    "code_repository_url",
                    "data_repository_url",
                    "author_comments",
                    "acad_field",
                    "specialties",
                    "topics",
                    "approaches",
                    "proceedings",
                    "code_metadata",
                ),
            },
        ),
        (
            "Authors",
            {
                "classes": ("collapse",),
                "fields": (
                    "submitted_by",
                    "authors",
                    "authors_claims",
                    "authors_false_claims",
                ),
            },
        ),
        (
            "Versioning",
            {
                "classes": ("collapse",),
                "fields": (
                    "followup_of",
                    "thread_hash",
                    "is_resubmission_of",
                    "list_of_changes",
                ),
            },
        ),
        (
            "Plagiarism",
            {
                "classes": ("collapse",),
                "fields": (
                    "internal_plagiarism_matches",
                    "iThenticate_plagiarism_report",
                ),
            },
        ),
        (
            "Conflicts of interest",
            {
                "classes": ("collapse",),
                "fields": ("needs_conflicts_update",),
            },
        ),
        (
            "Refereeing",
            {
                "classes": ("collapse",),
                "fields": (
                    "editor_in_charge",
                    ("visible_public", "visible_pool"),
                    "refereeing_cycle",
                    ("open_for_commenting", "open_for_reporting"),
                    "reporting_deadline",
                    "acceptance_date",
                    "referees_flagged",
                    "referees_suggested",
                    "remarks_for_editors",
                    "pdf_refereeing_pack",
                    "fellows",
                ),
            },
        ),
        (
            "Meta",
            {
                "classes": ("collapse",),
                "fields": ("metadata",),
            },
        ),
    )


@admin.register(EditorialAssignment)
class EditorialAssignmentAdmin(admin.ModelAdmin):
    search_fields = [
        "submission__title",
        "submission__author_list",
        "submission__preprint__identifier_w_vn_nr",
        "to__user__last_name",
    ]
    list_display = (
        "to",
        submission_short_title,
        "status",
        "date_created",
        "date_invited",
        "invitation_order",
    )
    date_hierarchy = "date_created"
    list_filter = ("status",)
    autocomplete_fields = [
        "submission",
        "to",
    ]


@admin.register(RefereeInvitation)
class RefereeInvitationAdmin(admin.ModelAdmin):
    search_fields = [
        "submission__title",
        "submission__author_list",
        "submission__preprint__identifier_w_vn_nr",
        "referee__user__last_name",
        "first_name",
        "last_name",
        "email_address",
    ]
    list_display = ("__str__", "accepted", "fulfilled", "cancelled")
    list_filter = (
        "accepted",
        "fulfilled",
        "cancelled",
    )
    date_hierarchy = "date_invited"
    autocomplete_fields = [
        "profile",
        "submission",
        "referee",
        "invited_by",
    ]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    search_fields = ["author__user__last_name", "submission__title"]
    list_display = (
        "author",
        "status",
        "doi_label",
        submission_short_title,
        "date_submitted",
    )
    list_display_links = ("author",)
    date_hierarchy = "date_submitted"
    list_filter = ("status",)
    readonly_fields = ("report_nr",)
    autocomplete_fields = [
        "submission",
        "vetted_by",
        "author",
    ]


@admin.register(EditorialCommunication)
class EditorialCommunicationAdmin(admin.ModelAdmin):
    search_fields = ["submission__title", "referee__user__last_name", "text"]
    autocomplete_fields = ["submission", "referee"]


class AlternativeRecommendationInline(admin.StackedInline):
    model = AlternativeRecommendation
    extra = 0
    min_num = 0
    autocomplete_fields = [
        "fellow",
        "for_journal",
    ]


@admin.register(EICRecommendation)
class EICRecommendationAdmin(admin.ModelAdmin):
    search_fields = ["submission__title"]
    list_filter = ("status",)
    list_display = (
        submission_short_title,
        submission_short_authors,
        "for_journal",
        "recommendation",
        "status",
        "active",
        "version",
    )
    inlines = [
        AlternativeRecommendationInline,
    ]
    autocomplete_fields = [
        "submission",
        "formulated_by",
        "eligible_to_vote",
        "voted_for",
        "voted_against",
        "voted_abstain",
    ]


@admin.register(EditorialDecision)
class EditorialDecisionAdmin(admin.ModelAdmin):
    search_fields = [
        "submission__title",
        "submission__author_list",
        "submission__preprint__identifier_w_vn_nr",
    ]
    list_filter = [
        "for_journal",
        "decision",
        "status",
    ]
    list_display = [
        submission_short_title,
        "for_journal",
        "decision",
        "taken_on",
        "status",
        "version",
    ]
    autocomplete_fields = [
        "submission",
        "for_journal",
    ]


@admin.register(SubmissionEvent)
class SubmissionEventAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        "submission",
    ]


@admin.register(RefereeIndication)
class RefereeIndicationAdmin(admin.ModelAdmin):
    search_fields = [
        "submission__title",
        "submission__preprint__identifier_w_vn_nr",
        "referee__first_name",
        "referee__last_name",
        "first_name",
        "last_name",
        "email_address",
    ]
    list_display = (
        "submission",
        "indicated_by",
        "indication",
        "referee_name",
    )
    list_filter = ("indication",)
    autocomplete_fields = [
        "submission",
        "indicated_by",
        "referee",
    ]

    def referee_name(self, obj):
        return (
            obj.referee.full_name
            if obj.referee
            else f"{obj.first_name} {obj.last_name}"
        )
