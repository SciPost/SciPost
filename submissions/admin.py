from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django import forms

from guardian.admin import GuardedModelAdmin

from comments.models import Comment
from submissions.models import Submission, EditorialAssignment, RefereeInvitation, Report,\
                               EditorialCommunication, EICRecommendation, SubmissionEvent,\
                               iThenticateReport
from scipost.models import Contributor


class CommentsGenericInline(GenericTabularInline):
    model = Comment


def submission_short_title(obj):
    return obj.submission.title[:30]


class iThenticateReportAdmin(admin.ModelAdmin):
    readonly_fields = ['doc_id']

    def has_add_permission(self, request):
        """ Don't add manually. This will gives conflict with the iThenticate db. """
        return False


admin.site.register(iThenticateReport, iThenticateReportAdmin)


class SubmissionAdminForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))
    authors_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))
    authors_false_claims = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.order_by('user__last_name'))

    class Meta:
        model = Submission
        fields = '__all__'


class SubmissionAdmin(GuardedModelAdmin):
    date_hierarchy = 'submission_date'
    form = SubmissionAdminForm
    list_display = ('title', 'author_list', 'status', 'submission_date', 'publication',)
    list_filter = ('status', 'discipline', 'submission_type',)
    search_fields = ['submitted_by__user__last_name', 'title', 'author_list', 'abstract']
    raw_id_fields = ('editor_in_charge', 'submitted_by')
    readonly_fields = ('arxiv_identifier_w_vn_nr', 'publication')

    # Admin fields should be added in the fieldsets
    radio_fields = {
        "discipline": admin.VERTICAL,
        "submitted_to_journal": admin.VERTICAL,
        "refereeing_cycle": admin.HORIZONTAL,
        "submission_type": admin.VERTICAL
    }
    fieldsets = (
        (None, {
            'fields': (
                'publication',
                'title',
                'abstract',
                'submission_type',
                ('arxiv_identifier_wo_vn_nr', 'arxiv_vn_nr', 'arxiv_identifier_w_vn_nr'),
                'arxiv_link'
                ),
        }),
        ('Versioning', {
            'fields': (
                'is_current',
                'is_resubmission',
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
                'refereeing_cycle',
                ('open_for_commenting', 'open_for_reporting'),
                'reporting_deadline',
                'acceptance_date',
                'referees_flagged',
                'referees_suggested',
                'remarks_for_editors',
                'submitted_to_journal',
                'proceedings',
                'pdf_refereeing_pack',
                'plagiarism_report',
                'fellows',
                'voting_fellows'),
        }),
        ('Meta', {
            'classes': ('collapse',),
            'fields': ('metadata', 'submission_date'),
        }),

    )


admin.site.register(Submission, SubmissionAdmin)


class EditorialAssignmentAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))

    class Meta:
        model = EditorialAssignment
        fields = '__all__'


class EditorialAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['submission__title', 'submission__author_list', 'to__user__last_name']
    list_display = ('to', submission_short_title, 'accepted', 'completed', 'date_created',)
    date_hierarchy = 'date_created'
    list_filter = ('accepted', 'deprecated', 'completed', )
    form = EditorialAssignmentAdminForm


admin.site.register(EditorialAssignment, EditorialAssignmentAdmin)


class RefereeInvitationAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))
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
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))

    class Meta:
        model = Report
        fields = '__all__'


class ReportAdmin(admin.ModelAdmin):
    search_fields = ['author__user__last_name', 'submission']
    list_display = ('author', 'status', submission_short_title, 'date_submitted', )
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
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))
    eligible_to_vote = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    voted_for = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    voted_against = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))
    voted_abstain = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Contributor.objects.filter(
            user__groups__name__in=['Editorial College'],
        ).order_by('user__last_name'))

    class Meta:
        model = EICRecommendation
        fields = '__all__'


class EICRecommendationAdmin(admin.ModelAdmin):
    search_fields = ['submission__title']
    form = EICRecommendationAdminForm


admin.site.register(EICRecommendation, EICRecommendationAdmin)

admin.site.register(SubmissionEvent)
