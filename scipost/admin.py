__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin
from django import forms

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission

from scipost.models import TOTPDevice, Contributor, Remark,\
                           AuthorshipClaim, PrecookedEmail,\
                           UnavailabilityPeriod

from organizations.admin import ContactInline
from production.admin import ProductionUserInline
from profiles.models import Profile
from submissions.models import Submission


class TOTPDeviceAdmin(admin.ModelAdmin):
    search_fields = [
        'user',
    ]
    autocomplete_fields = [
        'user',
    ]

admin.site.register(TOTPDevice)


class UnavailabilityPeriodAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'contributor',
    ]

admin.site.register(UnavailabilityPeriod, UnavailabilityPeriodAdmin)


class ContributorAdmin(admin.ModelAdmin):
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'profile__orcid_id'
    ]
    autocomplete_fields = [
        'profile',
        'user',
        'vetted_by',
        'duplicate_of',
    ]


class ContributorInline(admin.StackedInline):
    model = Contributor
    extra = 0
    min_num = 0
    autocomplete_fields = [
        'profile',
        'vetted_by',
        'duplicate_of',
    ]


class TOTPDeviceInline(admin.StackedInline):
    model = TOTPDevice
    extra = 0
    min_num = 0


class UserAdmin(UserAdmin):
    inlines = [
        ContributorInline,
        TOTPDeviceInline,
        ContactInline,
        ProductionUserInline
    ]
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'is_active', 'is_staff', 'is_duplicate']
    search_fields = ['username', 'last_name', 'email']

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
            ('submission', 'Submission'),
            ('recommendation', 'Recommendation'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'submission':
            return queryset.filter(submission__isnull=False)
        if self.value() == 'recommendation':
            return queryset.filter(recommendation__isnull=False)
        return None


def remark_text(obj):
    return obj.remark[:30]


def get_remark_type(remark):
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
    autocomplete_fields = [
        'contributor',
        'submission',
        'recommendation',
    ]

admin.site.register(Remark, RemarkAdmin)


class AuthorshipClaimAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'claimant',
        'submission',
        'commentary',
        'thesislink',
        'vetted_by',
    ]

admin.site.register(AuthorshipClaim, AuthorshipClaimAdmin)


admin.site.register(Permission)


class PrecookedEmailAdmin(admin.ModelAdmin):
    search_fields = ['email_subject', 'email_text', 'emailed_to']

admin.site.register(PrecookedEmail, PrecookedEmailAdmin)
