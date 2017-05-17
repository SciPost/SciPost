from django.contrib import admin, messages

from journals.models import ProductionStream, ProductionEvent
from journals.models import Journal, Volume, Issue, Publication, Deposit


admin.site.register(ProductionStream)


admin.site.register(ProductionEvent)


class JournalAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['__str__', 'doi_string', 'active']


admin.site.register(Journal, JournalAdmin)


class VolumeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'doi_string']


admin.site.register(Volume, VolumeAdmin)


class IssueAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'doi_string']


admin.site.register(Issue, IssueAdmin)


class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['title', 'author_list']
    list_display = ['title', 'author_list', 'in_issue', 'doi_string', 'publication_date']
    date_hierarchy = 'publication_date'
    list_filter = ['in_issue']


admin.site.register(Publication, PublicationAdmin)


class DepositAdmin(admin.ModelAdmin):
    list_display = ('doi_batch_id', 'publication', 'deposition_date',)
    readonly_fields = ('publication', 'doi_batch_id', 'metadata_xml', 'deposition_date',)
    actions = None

    def message_user(self, request, *args):
        return messages.warning(request, 'Sorry, Deposits are readonly.')

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False


admin.site.register(Deposit, DepositAdmin)
