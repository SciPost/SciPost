__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals import factories


class Command(BaseCommand):
    help = 'Create Issue objects using the factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            'number', action='store', default=0, type=int,
            help='Number of Issues to add')

    def handle(self, *args, **kwargs):
        self.create_issues(kwargs['number'])

    def create_issues(self, n):
        factories.IssueFactory.create_batch(n)
        self.stdout.write(self.style.SUCCESS('Successfully created {n} Issues.'.format(n=n)))
