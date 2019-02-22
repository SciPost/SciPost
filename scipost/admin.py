__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django import forms

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from scipost.models import Contributor, Remark,\
                           AuthorshipClaim, PrecookedEmail,\
                           EditorialCollege, EditorialCollegeFellowship, UnavailabilityPeriod

from organizations.admin import ContactInline
from partners.admin import ContactToUserInline
from production.admin import ProductionUserInline
from submissions.models import Submission


admin.site.register(UnavailabilityPeriod)


class ContributorAdmin(admin.ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'orcid_id',
        'affiliations__institution__name']


class ContributorInline(admin.StackedInline):
    model = Contributor
    extra = 0
    min_num = 0


class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline,
        ContactInline,
        ContactToUserInline, # TODO:PartnersDeprec remove
        ProductionUserInline
        ]
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'is_active', 'is_staff', 'is_duplicate']
    search_fields = ['last_name', 'email']

    def is_duplicate(self, obj):
        return obj.contributor.is_duplicate
    is_duplicate.short_description = 'Is duplicate?'
    is_duplicate.boolean = True

admin.site.unregister(User)
admin.site.register(Contributor, ContributorAdmin)
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
        queryset=Submission.objects.order_by('-preprint__identifier_w_vn_nr'))

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


admin.site.register(AuthorshipClaim)
admin.site.register(Permission)


class PrecookedEmailAdmin(admin.ModelAdmin):
    search_fields = ['email_subject', 'email_text', 'emailed_to']


admin.site.register(PrecookedEmail, PrecookedEmailAdmin)


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
