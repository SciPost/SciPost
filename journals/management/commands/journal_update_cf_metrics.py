__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals.models import Journal


class Command(BaseCommand):
    help = ('For all Journal model instances, '
            'this updates the calculated field `cf_metrics`')

    def handle(self, *args, **kwargs):
        for journal in Journal.objects.all():
            journal.update_cf_metrics()
        self.stdout.write(self.style.SUCCESS(
            'Successfully updated Journal:cf_metrics.'))
