__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.core import mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from django_celery_results.models import TaskResult


class Command(BaseCommand):
    help = 'Check if Celery is still running, or at least not failing.'

    def handle(self, *args, **kwargs):
        # check failed.
        compare_dt = timezone.now() - datetime.timedelta(hours=1)
        results_failed = TaskResult.objects.filter(
            status='FAILURE', date_done__gt=compare_dt).values_list('id', flat=True)
        if results_failed:
            # Mail failed
            body = 'Celery has failed task results. Failed IDs: {}'.format(
                ', '.join(results_failed))
            mail.mail_admins('Celery failed', body)
            self.stdout.write(
                self.style.SUCCESS('Celery failed, IDs: {}.'.format(', '.join(results_failed))))
        else:
            last_result = TaskResult.objects.filter(
                date_done__gt=compare_dt).order_by('date_done').last()
            if last_result and last_result.date_done < compare_dt:
                # Mail inactive
                body = 'No results for Celery found. Celery seems to be inactive.'
                body += ' Last result ID: {}'.format(last_result.id)
                mail.mail_admins('Celery inactive', body)
                self.stdout.write(
                    self.style.SUCCESS('Celery inactive, last ID: {}.'.format(last_result.id)))
        if not results_failed and not last_result:
            self.stdout.write(self.style.SUCCESS('Celery alive!'))
