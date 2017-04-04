import datetime

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from scipost.models import Contributor, Remark,\
                           DraftInvitation,\
                           AffiliationObject,\
                           SupportingPartner, SPBMembershipAgreement, RegistrationInvitation,\
                           AuthorshipClaim, PrecookedEmail,\
                           EditorialCollege, EditorialCollegeFellowship


class ContributorInline(admin.StackedInline):
    model = Contributor


class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline,
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


class RemarkAdmin(admin.ModelAdmin):
    search_fields = ['contributor', 'remark']
    list_display = [remark_text, 'contributor', 'date', get_remark_type]
    date_hierarchy = 'date'
    list_filter = [RemarkTypeListFilter]


admin.site.register(Remark, RemarkAdmin)


class DraftInvitationAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'processed']


admin.site.register(DraftInvitation, DraftInvitationAdmin)


class RegistrationInvitationAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'invitation_key']


admin.site.register(RegistrationInvitation, RegistrationInvitationAdmin)


admin.site.register(AuthorshipClaim)
admin.site.register(Permission)


class PrecookedEmailAdmin(admin.ModelAdmin):
    search_fields = ['email_subject', 'email_text', 'emailed_to']


admin.site.register(PrecookedEmail, PrecookedEmailAdmin)


class AffiliationObjectAdmin(admin.ModelAdmin):
    search_fields = ['country', 'institution', 'subunit']


admin.site.register(AffiliationObject, AffiliationObjectAdmin)


class SPBMembershipAgreementInline(admin.StackedInline):
    model = SPBMembershipAgreement


class SupportingPartnerAdmin(admin.ModelAdmin):
    search_fields = ['institution', 'institution_acronym',
                     'institution_address', 'contact_person']
    inlines = [
        SPBMembershipAgreementInline,
    ]


admin.site.register(SupportingPartner, SupportingPartnerAdmin)


class EditorialCollegeAdmin(admin.ModelAdmin):
    search_fields = ['discipline', 'member']


admin.site.register(EditorialCollege, EditorialCollegeAdmin)


def college_fellow_is_active(fellow):
    '''Check if fellow is currently active.'''
    return fellow.is_active()


class EditorialCollegeFellowshipAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'college', college_fellow_is_active)
    list_filter = ('college', 'affiliation')
    search_fields = ['college__discipline',
                     'contributor__user__first_name', 'contributor__user__last_name']
    fields = ('contributor', 'college', 'start_date', 'until_date', 'affiliation', )

    college_fellow_is_active.boolean = True


admin.site.register(EditorialCollegeFellowship, EditorialCollegeFellowshipAdmin)
