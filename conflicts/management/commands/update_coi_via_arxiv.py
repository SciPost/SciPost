__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from scipost.models import Contributor
from submissions.models import Submission

from ...services import ArxivCaller


class Command(BaseCommand):
    """Update Conflict of Interests using arXiv API."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--arxiv', action='store', default=0, type=str,
            dest='arxiv', help='ArXiv id of Submission to force update of conflicts.')

    def handle(self, *args, **options):
        if options['arxiv']:
            submissions = Submission.objects.filter(preprint__identifier_w_vn_nr=options['arxiv'])
        else:
            submissions = Submission.objects.needs_conflicts_update()

        for sub in submissions:
            fellow_ids = sub.fellows.values_list('id', flat=True)
            fellows = Contributor.objects.filter(fellowships__id__in=fellow_ids)
            if 'entries' in sub.metadata:
                caller = ArxivCaller(sub.metadata['entries'][0]['authors'])
                caller.compare_to(fellows)
                caller.add_to_db(sub)
                Submission.objects.filter(id=sub.id).update(needs_conflicts_update=False)
