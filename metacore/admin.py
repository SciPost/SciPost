from django.contrib import admin
from django.contrib import messages
from .models import Citable, CitableWithDOI, Journal
from .services import get_crossref_test, import_journal_full, get_crossref_work_count

# Register your models here.
class JournalAdmin(admin.ModelAdmin):
    fields = ('name', 'ISSN_digital', 'last_full_sync')
    list_display = ('name', 'ISSN_digital', 'last_full_sync', 'count_metacore', 'count_crossref')
    actions = ['import_full', 'update_counts']

    def import_full(self, request, queryset):
        """ Starts background task to import all works by this journal """

        for journal in queryset:
            t = import_journal_full(journal.ISSN_digital)
            messages.add_message(request, messages.INFO, 'Import task for journal {} added. Go to Background Tasks -> Tasks in admin to view them'.format(journal.name))

        messages.add_message(request, messages.WARNING, 'Make sure to start the tasks by running ./manage.py process_tasks')
    def update_counts(self, request, queryset):
        for journal in queryset:
            journal.count_metacore = Citable.objects(metadata__ISSN=journal.ISSN_digital).count()
            journal.count_crossref = get_crossref_work_count(journal.ISSN_digital)
            journal.save()

        messages.add_message(request, messages.INFO, 'Counts updated.')

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

admin.site.register(Journal, JournalAdmin)
