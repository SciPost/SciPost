__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django.db.models import Q
from django import forms

from guardian.admin import GuardedModelAdmin

from submissions.models import (
    Submission, EditorialAssignment, RefereeInvitation, Report, EditorialCommunication,
    EICRecommendation, SubmissionEvent, iThenticateReport)
from scipost.models import Contributor


def submission_short_title(obj):
    return obj.submission.title[:30]


class iThenticateReportAdmin(admin.ModelAdmin):
    list_display = ['doc_id', 'to_submission', 'status']
    list_filter = ['status']


admin.site.register(iThenticateReport, iThenticateReportAdmin)


class SubmissionAdminForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.nonduplicates().order_by('user__last_name'))
    authors_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.nonduplicates().order_by('user__last_name'))
    authors_false_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.nonduplicates().order_by('user__last_name'))
    is_resubmission_of = forms.ModelChoiceField(
        required=False,
        queryset=Submission.objects.order_by('-preprint__identifier_w_vn_nr'))

    class Meta:
        model = Submission
        fields = '__all__'
        # fields = ['preprint', 'author_comments', 'author_list',
        #           'discipline', 'domain', 'editor_in_charge',
        #           'list_of_changes', 'open_for_commenting', 'open_for_reporting',
        #           'referees_flagged', 'referees_suggested', 'remarks_for_editors',
        #           'reporting_deadline', 'secondary_areas',
        #           'status', 'is_current', 'visible_public', 'visible_pool',
        #           'thread_hash', '_is_resubmission', 'refereeing_cycle',
        #           'fellows', 'subject_area', 'submission_type', 'submitted_by',
        #           'voting_fellows', 'submitted_to', 'proceedings',
        #           'title', 'abstract', 'comments', 'needs_conflicts_update',
        #           'plagiarism_report',
        #           'arxiv_identifier_w_vn_nr', 'arxiv_identifier_wo_vn_nr',
        #           'arxiv_vn_nr', 'arxiv_link', 'pdf_refereeing_pack',
        #           'metadata', 'submission_date', 'acceptance_date',
        #           'latest_activity', 'update_search_index',
        #           'topics', 'needs_conflicts_update'

class SubmissionAdmin(GuardedModelAdmin):
    date_hierarchy = 'submission_date'
    form = SubmissionAdminForm
    list_display = ('title', 'author_list', 'preprint', 'submitted_to',
                    'status', 'visible_public', 'visible_pool', 'refereeing_cycle',
                    'submission_date', 'publication')
    list_filter = ('status', 'discipline', 'submission_type', 'submitted_to')
    search_fields = ['submitted_by__user__last_name', 'title', 'author_list', 'abstract']
    raw_id_fields = ('editor_in_charge', 'submitted_by')
    readonly_fields = ('publication',)

    # Admin fields should be added in the fieldsets
    radio_fields = {
        "discipline": admin.VERTICAL,
        "submitted_to": admin.VERTICAL,
        "refereeing_cycle": admin.HORIZONTAL,
        "submission_type": admin.VERTICAL
    }
    fieldsets = (
        (None, {
            'fields': (
                'preprint',
                'publication',
                'title',
                'abstract',
                'submission_type'),
        }),
        ('Versioning', {
            'fields': (
                'thread_hash',
                'is_current',
                '_is_resubmission',
                'is_resubmission_of',
                'list_of_changes'),
        }),
        ('Submission details', {
            'classes': ('collapse',),
            'fields': (
                'author_comments',
                'discipline',
                'domain',
                'subject_area',
                'secondary_areas',
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


class EditorialAssignmentAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-preprint__identifier_w_vn_nr'))

    class Meta:
        model = EditorialAssignment
        fields = '__all__'


class EditorialAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list', 'to__user__last_name']
    list_display = (
        'to', submission_short_title, 'status', 'date_created', 'date_invited', 'invitation_order')
    date_hierarchy = 'date_created'
    list_filter = ('status',)
    form = EditorialAssignmentAdminForm


admin.site.register(EditorialAssignment, EditorialAssignmentAdmin)


class RefereeInvitationAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-preprint__identifier_w_vn_nr'))
    referee = forms.ModelChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))

    class Meta:
        model = RefereeInvitation
        fields = '__all__'


class RefereeInvitationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list',
                     'referee__user__last_name',
                     'first_name', 'last_name', 'email_address']
    list_display = ('__str__', 'accepted', )
    list_filter = ('accepted', 'fulfilled', 'cancelled',)
    date_hierarchy = 'date_invited'
    form = RefereeInvitationAdminForm


admin.site.register(RefereeInvitation, RefereeInvitationAdmin)


class ReportAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-preprint__identifier_w_vn_nr'))

    class Meta:
        model = Report
        fields = '__all__'


class ReportAdmin(admin.ModelAdmin):
    search_fields = ['author__user__last_name', 'submission__title']
    list_display = ('author', 'status', 'doi_label', submission_short_title, 'date_submitted', )
    list_display_links = ('author',)
    date_hierarchy = 'date_submitted'
    list_filter = ('status',)
    readonly_fields = ('report_nr',)
    form = ReportAdminForm


admin.site.register(Report, ReportAdmin)


class EditorialCommunicationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'referee__user__last_name', 'text']


admin.site.register(EditorialCommunication, EditorialCommunicationAdmin)


class EICRecommendationAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-preprint__identifier_w_vn_nr'))
    eligible_to_vote = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            Q(user__groups__name__in=['Editorial College']) |
            Q(fellowships__isnull=False),
        ).distinct().order_by('user__last_name'))
    voted_for = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            Q(user__groups__name__in=['Editorial College']) |
            Q(fellowships__isnull=False),
        ).distinct().order_by('user__last_name'))
    voted_against = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            Q(user__groups__name__in=['Editorial College']) |
            Q(fellowships__isnull=False),
        ).distinct().order_by('user__last_name'))
    voted_abstain = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            Q(user__groups__name__in=['Editorial College']) |
            Q(fellowships__isnull=False),
        ).distinct().order_by('user__last_name'))

    class Meta:
        model = EICRecommendation
        fields = '__all__'


class EICRecommendationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title']
    list_filter = ('status',)
    list_display = (submission_short_title, 'recommendation', 'status', 'active', 'version')
    form = EICRecommendationAdminForm


admin.site.register(EICRecommendation, EICRecommendationAdmin)

admin.site.register(SubmissionEvent)
