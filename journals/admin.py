from django.contrib import admin, messages

from journals.models import Journal, Volume, Issue, Publication, Deposit


class JournalAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Journal, JournalAdmin)


class VolumeAdmin(admin.ModelAdmin):
    pass


admin.site.register(Volume, VolumeAdmin)


class IssueAdmin(admin.ModelAdmin):
    pass


admin.site.register(Issue, IssueAdmin)


class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['title', 'author_list']


admin.site.register(Publication, PublicationAdmin)


class DepositAdmin(admin.ModelAdmin):
    list_display = ('doi_batch_id', 'publication', 'deposition_date',)
    readonly_fields = ('publication', 'doi_batch_id', 'metadata_xml', 'deposition_date',)
    actions = None

    def message_user(self, request, *args):
        return messages.warning(request, 'Sorry, Deposit\'s are readonly.')

    def has_add_permission(self, *args):
        return False

    def has_delete_permission(self, *args):
        return False


admin.site.register(Deposit, DepositAdmin)
