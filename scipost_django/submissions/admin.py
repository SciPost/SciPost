__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django import forms

from django.db.models.query import QuerySet
from guardian.admin import GuardedModelAdmin
from ethics.admin import GenAIDisclosureInline, RedFlagInline

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
from submissions.models.assignment import ConditionalAssignmentOffer


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


class InternalPlagiarismAssessmentInline(admin.TabularInline):
    model = InternalPlagiarismAssessment


class iThenticatePlagiarismAssessmentInline(admin.TabularInline):
    model = iThenticatePlagiarismAssessment


class QualificationInline(admin.TabularInline):
    model = Qualification
    extra = 0
    min_num = 0
    autocomplete_fields = ["submission", "fellow"]
    fields = ["submission", "fellow", "expertise_level", "datetime"]


class ReadinessInline(admin.TabularInline):
    model = Readiness
    extra = 0
    min_num = 0
    autocomplete_fields = ["submission", "fellow"]
    fields = ["submission", "fellow", "status", "datetime"]


class SubmissionClearanceInline(admin.TabularInline):
    model = SubmissionClearance
    extra = 0
    min_num = 0
    autocomplete_fields = [
        "profile",
        "submission",
        "asserted_by",
    ]
    fields = ["profile", "submission", "asserted_by", "asserted_on"]


class SubmissionAuthorProfileInline(admin.TabularInline):
    model = SubmissionAuthorProfile
    extra = 0
    exclude = ["affiliations"]
    autocomplete_fields = ["profile"]


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


class SubmissionEventInline(admin.TabularInline):
    model = SubmissionEvent
    extra = 0
    autocomplete_fields = ["submission"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "text":
            kwargs["widget"] = forms.Textarea(attrs={"rows": 2, "cols": 80})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ConditionalAssignmentOfferInline(admin.TabularInline):
    model = ConditionalAssignmentOffer
    extra = 0
    autocomplete_fields = [
        "submission",
        "offered_by",
        "accepted_by",
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "condition_details":
            kwargs["widget"] = forms.Textarea(attrs={"rows": 2, "cols": 40})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class RefereeIndicationInline(admin.TabularInline):
    model = RefereeIndication
    extra = 1
    autocomplete_fields = [
        "submission",
        "referee",
        "indicated_by",
    ]
    fields = [
        "submission",
        "referee",
        "indicated_by",
        "indication",
        "first_name",
        "last_name",
        "email_address",
        "affiliation",
        "reason",
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "reason":
            kwargs["widget"] = forms.Textarea(attrs={"rows": 1, "cols": 20})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ReportAuthorStatusTabularInline(admin.TabularInline):
    model = Report
    extra = 0
    min_num = 0
    autocomplete_fields = ["author"]
    fields = [
        "author",
        "status",
        "invited",
        "anonymous",
    ]


class RefereeInvitationTabularInline(admin.TabularInline):
    model = RefereeInvitation
    extra = 0
    min_num = 0
    autocomplete_fields = ["referee"]
    fields = [
        "referee",
        "email_address",
        "accepted",
        "cancelled",
        "fulfilled",
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
        "submitted_by__dbuser__last_name",
        "title",
        "author_list",
        "abstract",
        "preprint__identifier_w_vn_nr",
        "thread_hash",
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
        GenAIDisclosureInline,
        CollectionInline,
        InternalPlagiarismAssessmentInline,
        iThenticatePlagiarismAssessmentInline,
        SubmissionAuthorProfileInline,
        SubmissionClearanceInline,
        QualificationInline,
        ReadinessInline,
        ConditionalAssignmentOfferInline,
        RefereeIndicationInline,
        RefereeInvitationTabularInline,
        ReportAuthorStatusTabularInline,
        SubmissionTieringInline,
        RedFlagInline,
        SubmissionEventInline,
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
            "Coauthorships",
            {
                "classes": ("collapse",),
                "fields": ("needs_coauthorships_update",),
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
                    "assignment_deadline",
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
        "to__dbuser__last_name",
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
        "referee__first_name",
        "referee__last_name",
        "email_address",
        "invitation_key",
    ]
    list_display = ("__str__", "accepted", "fulfilled", "cancelled")
    list_filter = (
        "accepted",
        "fulfilled",
        "cancelled",
    )
    date_hierarchy = "date_invited"
    autocomplete_fields = [
        "submission",
        "referee",
        "invited_by",
    ]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    search_fields = [
        "author__dbuser__last_name",
        "submission__title",
        "submission__preprint__identifier_w_vn_nr",
    ]
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
    inlines = [
        GenAIDisclosureInline,
    ]


@admin.register(EditorialCommunication)
class EditorialCommunicationAdmin(admin.ModelAdmin):
    search_fields = [
        "submission__title",
        "submission__preprint__identifier_w_vn_nr",
        "referee__dbuser__last_name",
        "text",
    ]
    list_display = [
        "text_trunc",
        "author",
        "recipient",
        "submission_title",
        "timestamp",
    ]
    list_filter = ("comtype",)
    autocomplete_fields = ["submission", "referee"]

    def get_queryset(self, request) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "submission",
                "submission__submitted_by__profile",
                "submission__editor_in_charge__profile",
                "referee",
            )
        )

    def submission_title(self, obj):
        return (
            obj.submission.title[:50] + "..."
            if len(obj.submission.title) > 50
            else obj.submission.title
        )

    def text_trunc(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    def author(self, obj):
        return obj.author_name

    def recipient(self, obj):
        return obj.recipient_name


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
    search_fields = [
        "submission__title",
        "submission__preprint__identifier_w_vn_nr",
        "formulated_by__profile__last_name",
        "formulated_by__profile__first_name",
    ]
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
    search_fields = [
        "submission__title",
        "submission__author_list",
        "submission__preprint__identifier_w_vn_nr",
    ]
    list_display = [
        "submission",
        "event",
        "text",
    ]
    list_filter = [
        "event",
    ]
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
