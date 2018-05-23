from django.contrib import admin
from django.contrib import messages
from .models import Citable, CitableWithDOI, Journal
from .services import import_journal_full, import_journal_incremental, get_crossref_work_count, add_journal_to_existing

# Register your models here.
class JournalAdmin(admin.ModelAdmin):
    fields = ('name', 'ISSN_digital', 'last_full_sync')
    list_display = ('name', 'ISSN_digital', 'last_full_sync', 'count_metacore', 'count_crossref', 'last_update')
    actions = ['import_full', 'import_incremental', 'update_counts', 'add_journal_to_items', 'delete_all_citables']

    def import_full(self, request, queryset):
        """ Starts background task to import all works by this journal """

        for journal in queryset:
            t = import_journal_full(journal.ISSN_digital)
            messages.add_message(request, messages.INFO, 'Import task for journal {} added. Go to Background Tasks -> Tasks in admin to view'.format(journal.name))

        messages.add_message(request, messages.WARNING, 'Make sure that "./manage.py process_tasks" is running (otherwise start it).')

    def import_incremental(self, request, queryset):
        """ Starts background task to import all works by this journal """

        for journal in queryset:
            if journal.last_update:
                t = import_journal_incremental(journal.ISSN_digital, journal.last_update.strftime('%Y-%m-%d'))
                messages.add_message(request, messages.INFO, 'Import task for journal {} added. Go to Background Tasks -> Tasks in admin to view'.format(journal.name))
            else:
                messages.add_message(request, messages.INFO, 'Incremental import task for journal {} could not be started, since date of last full sync is not set.'.format(journal.name))

        messages.add_message(request, messages.WARNING, 'Make sure that "./manage.py process_tasks" is running (otherwise start it).')

    def update_counts(self, request, queryset):
        for journal in queryset:
            journal.count_metacore = Citable.objects(metadata__ISSN=journal.ISSN_digital).count()
            journal.count_crossref = get_crossref_work_count(journal.ISSN_digital)
            journal.save()

        messages.add_message(request, messages.INFO, 'Counts updated.')

    def add_journal_to_items(self, request, queryset):
        for journal in queryset:
            add_journal_to_existing(journal.ISSN_digital)
            messages.add_message(request, messages.INFO, '"Add journal" task for journal {} added. Go to Background Tasks -> Tasks in admin to view'.format(journal.name))

        messages.add_message(request, messages.WARNING, 'Make sure that "./manage.py process_tasks" is running (otherwise start it).')

    def delete_all_citables(self, request, queryset):
        for journal in queryset:
            journal.purge_citables()
            messages.add_message(request, messages.INFO, 'All citables from journal "{}" deleted.'.format(journal.name))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

admin.site.register(Journal, JournalAdmin)
