__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals import factories


class Command(BaseCommand):
    help = 'Create Journal objects using the factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            'number', action='store', default=0, type=int,
            help='Number of Journals to add')

    def handle(self, *args, **kwargs):
        self.create_journals(kwargs['number'])

    def create_journals(self, n):
        factories.JournalFactory.create_batch(n)
        self.stdout.write(self.style.SUCCESS('Successfully created {n} Journals.'.format(n=n)))
