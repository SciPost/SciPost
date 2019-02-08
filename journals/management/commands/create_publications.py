__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals.constants import SCIPOST_JOURNALS_SUBMIT
from journals.factories import PublicationFactory


class Command(BaseCommand):
    help = 'Create random Publication objects by using the factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            'number', action='store', default=0, type=int,
            help='Number of publications to add',
        )
        parser.add_argument(
            '--journal', choices=[i[0] for i in SCIPOST_JOURNALS_SUBMIT],
            action='store', dest='journal',
            help='The name of the specific Journal to add the Publications to',
        )

    def handle(self, *args, **kwargs):
        if kwargs['number'] > 0:
            journal = None
            if kwargs.get('journal'):
                journal = kwargs['journal']
            self.create_publications(kwargs['number'], journal=journal)

    def create_publications(self, n, journal=None):
        PublicationFactory.create_batch(n, journal=journal)
        self.stdout.write(self.style.SUCCESS('Successfully created {n} Publications.'.format(n=n)))
