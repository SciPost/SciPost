__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from scipost import factories


class Command(BaseCommand):
    help = 'Create random Contributor objects using the factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            'number', action='store', default=0, type=int,
            help='Number of Contributors to add')

    def handle(self, *args, **kwargs):
        self.create_contributors(kwargs['number'])

    def create_contributors(self, n):
        factories.ContributorFactory.create_batch(n)
        self.stdout.write(self.style.SUCCESS('Successfully created {n} Contributors.'.format(n=n)))
