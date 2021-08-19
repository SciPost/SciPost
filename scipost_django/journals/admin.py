__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import admin, messages
from django import forms

from journals.models import Journal, Volume, Issue, Publication, \
    Deposit, DOAJDeposit, GenericDOIDeposit, Reference, PublicationAuthorsTable,\
    OrgPubFraction, PublicationUpdate, SubmissionTemplate

from scipost.models import Contributor
from submissions.models import Submission


class SubmissionTemplateInline(admin.TabularInline):
    model = SubmissionTemplate
    extra = 0


class JournalAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['__str__', 'doi_string', 'active']
    inlines = [
        SubmissionTemplateInline,
    ]

admin.site.register(Journal, JournalAdmin)


class VolumeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'doi_string']


admin.site.register(Volume, VolumeAdmin)


class IssueAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'doi_string']
    search_fields = [
        'in_journal__name',
        'in_volume__in_journal__name',
        'doi_label',
    ]

admin.site.register(Issue, IssueAdmin)


class ReferenceInline(admin.TabularInline):
    model = Reference
    extra = 0


class AuthorsInline(admin.TabularInline):
    model = PublicationAuthorsTable
    extra = 0
    autocomplete_fields = [
        'profile',
        'affiliations',
    ]


class OrgPubFractionInline(admin.TabularInline):
    model = OrgPubFraction
    list_display = ('organization', 'publication', 'fraction')
    autocomplete_fields = [
        'organization',
    ]


class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['title', 'author_list', 'doi_label']
    list_display = [
        'title', 'author_list',
        'in_issue', 'doi_string',
        'publication_date', 'status']
    date_hierarchy = 'publication_date'
    list_filter = ['in_issue']
    inlines = [AuthorsInline, ReferenceInline, OrgPubFractionInline]
    autocomplete_fields = [
        'accepted_submission',
        'grants',
        'funders_generic',
        'topics',
    ]

admin.site.register(Publication, PublicationAdmin)


class PublicationProxyMetadata(Publication):
    search_fields = ['title', 'author_list', 'doi_label']
    list_display = [
        'title', 'author_list',
        'in_issue', 'doi_string',
        'publication_date', 'status']

    class Meta:
        proxy = True
        verbose_name = 'Publication metadata'
        verbose_name_plural = 'Publication metadata'


class PublicationProxyMetadataAdmin(admin.ModelAdmin):
    fields = ['metadata', 'metadata_xml', 'metadata_DOAJ', 'BiBTeX_entry']
    search_fields = ['title', 'author_list', 'doi_label']
    list_display = [
        'title', 'author_list',
        'in_issue', 'doi_string',
        'publication_date', 'status']


admin.site.register(PublicationProxyMetadata, PublicationProxyMetadataAdmin)


class DepositAdmin(admin.ModelAdmin):
    list_display = ('publication', 'timestamp', 'doi_batch_id', 'deposition_date',)
    readonly_fields = ('publication', 'doi_batch_id', 'metadata_xml', 'deposition_date',)
    actions = None

    def message_user(self, request, *args):
        return messages.warning(request, 'Sorry, Deposits are readonly.')

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False

admin.site.register(Deposit, DepositAdmin)


class DOAJDepositAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'publication',
    ]

admin.site.register(DOAJDeposit, DOAJDepositAdmin)


admin.site.register(GenericDOIDeposit)


class PublicationUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'publication',
    ]

admin.site.register(PublicationUpdate, PublicationUpdateAdmin)
