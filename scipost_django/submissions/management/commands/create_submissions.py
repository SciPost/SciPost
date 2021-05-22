__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from submissions import factories


class Command(BaseCommand):
    help = 'Create random Submission objects by using the factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            'number', action='store', default=0, type=int,
            help='Number of submissions to add',
        )
        parser.add_argument(
            '-s', '--status',
            choices=['unassigned', 'assigned', 'resubmitted', 'resubmission', 'published'],
            action='store', dest='status', default='assigned',
            help='Current status of the Submission',
        )

    def handle(self, *args, **kwargs):
        if kwargs['number']:
            self.create_submissions(kwargs['number'], status=kwargs['status'])

    def create_submissions(self, n, status='assigned'):
        if status == 'unassigned':
            factories.UnassignedSubmissionFactory.create_batch(n)
        elif status == 'assigned':
            factories.EICassignedSubmissionFactory.create_batch(n)
        elif status == 'resubmitted':
            factories.ResubmittedSubmissionFactory.create_batch(n)
        elif status == 'resubmission':
            factories.ResubmissionFactory.create_batch(n)
        elif status == 'published':
            factories.PublishedSubmissionFactory.create_batch(n)
        self.stdout.write(self.style.SUCCESS('Successfully created {n} Submissions.'.format(n=n)))
