__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json

from django.contrib import admin
from django.contrib import messages

from celery.result import AsyncResult
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .models import Citable, Journal
from .services import (
    import_journal_full, import_journal_incremental, get_crossref_work_count,
    add_journal_to_existing)


class JournalAdmin(admin.ModelAdmin):
    fields = ('name', 'ISSN_digital', 'last_full_sync')
    list_display = (
        'name', 'ISSN_digital', 'last_full_sync', 'count_metacore',
        'count_crossref', 'last_update', 'task_status')
    actions = [
        'import_full', 'scheduled_import_incremental', 'import_incremental',
        'update_counts', 'add_journal_to_items', 'delete_all_citables']

    def import_full(self, request, queryset):
        """ Starts background task to import all works by this journal """

        for journal in queryset:
            # Celery Async version
            task = import_journal_full.delay(journal.ISSN_digital)
            journal.last_task_id = task.id
            journal.save()

            messages.add_message(
                request, messages.INFO, 'Import task for journal {} added.'.format(journal.name))


    def import_incremental(self, request, queryset):
        """Starts background task to import all works by this journal."""

        for journal in queryset:
            if journal.last_full_sync:
                task = import_journal_incremental.delay(
                    journal.ISSN_digital, journal.last_full_sync.strftime('%Y-%m-%d'))
                journal.last_task_id = task.id
                journal.save()
                messages.add_message(
                    request, messages.INFO,
                    'Import task for journal {} added.'.format(journal.name))
            else:
                messages.add_message(
                    request, messages.WARNING,
                    ('Incremental import task for journal {} could not be started, '
                     'since date of last full sync is not set.'.format(journal.name)))

    def scheduled_import_incremental(self, request, queryset):
        """Starts background task to import all works by this journal and repeats every day."""
        # TODO: make sure the from_date gets updated!

        schedule, __ = IntervalSchedule.objects.get_or_create(
            every=1, period=IntervalSchedule.DAYS)

        for journal in queryset:
            last_sync = ''
            if journal.last_full_sync:
                last_sync = journal.last_full_sync.strftime('%Y-%m-%d')

            task, created = PeriodicTask.objects.get_or_create(
                interval=schedule,
                name='Inc. import {}'.format(journal.name),
                task='metacore.services.import_journal_incremental',
                args=json.dumps([journal.ISSN_digital, last_sync]))
            PeriodicTask.objects.filter(id=task.id).update(enabled=True)

            #TODO: figure out a way to put the individual task id in the journal
            # everytime the scheduled task fires
            journal.last_task_id = ''
            journal.save()

            if created:
                txt = 'Repeating import task for journal {} added.'.format(journal.name)
            elif task.enabled:
                txt = 'Repeating import task for journal {} already exists.'.format(journal.name)
            else:
                txt = 'Repeating import task for journal {} activated.'.format(journal.name)
            txt += ' Go to Periodic Tasks in admin to view.'.format(journal.name)

            messages.add_message(request, messages.INFO, txt)

    def update_counts(self, request, queryset):
        for journal in queryset:
            journal.count_metacore = Citable.objects(metadata__ISSN=journal.ISSN_digital).count()
            journal.count_crossref = get_crossref_work_count(journal.ISSN_digital)
            journal.save()

        messages.add_message(request, messages.INFO, 'Counts updated.')

    def add_journal_to_items(self, request, queryset):
        for journal in queryset:
            add_journal_to_existing(journal.ISSN_digital)
            messages.add_message(
                request, messages.INFO,
                ('"Add journal" task for journal {} added. Go to Background'
                 ' Tasks -> Tasks in admin to view'.format(journal.name)))


    def delete_all_citables(self, request, queryset):
        for journal in queryset:
            journal.purge_citables()
            messages.add_message(
                request, messages.INFO,
                'All citables from journal "{}" deleted.'.format(journal.name))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def task_status(self, journal):
        if journal.last_task_id:
            task = AsyncResult(journal.last_task_id)
            if task:
                return task.result
        return ''

admin.site.register(Journal, JournalAdmin)
