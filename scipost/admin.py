from django.contrib import admin
from django import forms

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from scipost.models import Contributor, Remark,\
                           DraftInvitation,\
                           AffiliationObject,\
                           RegistrationInvitation,\
                           AuthorshipClaim, PrecookedEmail,\
                           EditorialCollege, EditorialCollegeFellowship, UnavailabilityPeriod

from journals.models import Publication
from partners.admin import ContactToUserInline
from submissions.models import Submission


admin.site.register(UnavailabilityPeriod)


class ContributorInline(admin.StackedInline):
    model = Contributor
    extra = 0
    min_num = 0


class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline,
        ContactToUserInline,
        ]
    search_fields = ['last_name', 'email']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class RemarkTypeListFilter(admin.SimpleListFilter):
    title = 'Remark Type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples to define the filter values in the Admin UI.
        """
        return (
            ('feedback', 'Feedback'),
            ('nomination', 'Nomination'),
            ('motion', 'Motion'),
            ('submission', 'Submission'),
            ('recommendation', 'Recommendation'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'feedback':
            return queryset.filter(feedback__isnull=False)
        if self.value() == 'nomination':
            return queryset.filter(nomination__isnull=False)
        if self.value() == 'motion':
            return queryset.filter(motion__isnull=False)
        if self.value() == 'submission':
            return queryset.filter(submission__isnull=False)
        if self.value() == 'recommendation':
            return queryset.filter(recommendation__isnull=False)
        return None


def remark_text(obj):
    return obj.remark[:30]


def get_remark_type(remark):
    if remark.feedback:
        return 'Feedback'
    if remark.nomination:
        return 'Nomination'
    if remark.motion:
        return 'Motion'
    if remark.submission:
        return 'Submission'
    if remark.recommendation:
        return 'Recommendation'
    return ''


class RemarkAdminForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        required=False,
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))

    class Meta:
        model = Remark
        fields = '__all__'


class RemarkAdmin(admin.ModelAdmin):
    search_fields = ['contributor', 'remark']
    list_display = [remark_text, 'contributor', 'date', get_remark_type]
    date_hierarchy = 'date'
    list_filter = [RemarkTypeListFilter]
    form = RemarkAdminForm


admin.site.register(Remark, RemarkAdmin)


class DraftInvitationAdminForm(forms.ModelForm):
    cited_in_submission = forms.ModelChoiceField(
        required=False,
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))
    cited_in_publication = forms.ModelChoiceField(
        required=False,
        queryset=Publication.objects.order_by('-publication_date'))

    class Meta:
        model = DraftInvitation
        fields = '__all__'


class DraftInvitationAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'processed']
    form = DraftInvitationAdminForm


admin.site.register(DraftInvitation, DraftInvitationAdmin)


class RegistrationInvitationAdminForm(forms.ModelForm):
    cited_in_submission = forms.ModelChoiceField(
        required=False,
        queryset=Submission.objects.order_by('-arxiv_identifier_w_vn_nr'))
    cited_in_publication = forms.ModelChoiceField(
        required=False,
        queryset=Publication.objects.order_by('-publication_date'))

    class Meta:
        model = RegistrationInvitation
        fields = '__all__'


class RegistrationInvitationAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'invitation_key']
    list_display = ['__str__', 'invitation_type', 'invited_by', 'responded']
    list_filter = ['invitation_type', 'message_style', 'responded', 'declined']
    date_hierarchy = 'date_sent'
    form = RegistrationInvitationAdminForm


admin.site.register(RegistrationInvitation, RegistrationInvitationAdmin)
admin.site.register(AuthorshipClaim)
admin.site.register(Permission)


class PrecookedEmailAdmin(admin.ModelAdmin):
    search_fields = ['email_subject', 'email_text', 'emailed_to']


admin.site.register(PrecookedEmail, PrecookedEmailAdmin)


class AffiliationObjectAdmin(admin.ModelAdmin):
    search_fields = ['country', 'institution', 'subunit']


admin.site.register(AffiliationObject, AffiliationObjectAdmin)


class EditorialCollegeAdmin(admin.ModelAdmin):
    search_fields = ['discipline', 'member']


admin.site.register(EditorialCollege, EditorialCollegeAdmin)


def college_fellow_is_active(fellow):
    '''Check if fellow is currently active.'''
    return fellow.is_active()

class EditorialCollegeFellowshipAdminForm(forms.ModelForm):
    contributor = forms.ModelChoiceField(
        queryset=Contributor.objects.order_by('user__last_name'))

    class Meta:
        model = EditorialCollegeFellowship
        fields = '__all__'


class EditorialCollegeFellowshipAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'college', college_fellow_is_active)
    list_filter = ('college', 'affiliation')
    search_fields = ['college__discipline',
                     'contributor__user__first_name', 'contributor__user__last_name']
    fields = ('contributor', 'college', 'start_date', 'until_date', 'affiliation', )

    college_fellow_is_active.boolean = True
    form = EditorialCollegeFellowshipAdminForm


admin.site.register(EditorialCollegeFellowship, EditorialCollegeFellowshipAdmin)
