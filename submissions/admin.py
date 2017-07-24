from django.contrib import admin
from django import forms

from guardian.admin import GuardedModelAdmin

from submissions.models import Submission, EditorialAssignment, RefereeInvitation, Report,\
                               EditorialCommunication, EICRecommendation

from scipost.models import Contributor


def submission_short_title(obj):
    return obj.submission.title[:30]


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
    search_fields = ['submitted_by__user__last_name', 'title', 'author_list', 'abstract']
    list_display = ('title', 'author_list', 'status', 'submission_date', 'publication',)
    date_hierarchy = 'submission_date'
    list_filter = ('status', 'discipline', 'submission_type', )
    form = SubmissionAdminForm


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
