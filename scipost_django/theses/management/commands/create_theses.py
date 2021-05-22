__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from theses import factories


class Command(BaseCommand):
    help = 'Create random Thesis objects using the factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            'number', action='store', default=0, type=int,
            help='Number of Theses to add')

    def handle(self, *args, **kwargs):
        self.create_theses(kwargs['number'])

    def create_theses(self, n):
        factories.ThesisLinkFactory.create_batch(n)
        self.stdout.write(self.style.SUCCESS('Successfully created {n} Theses.'.format(n=n)))
