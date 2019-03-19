__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.db.models import Q

from profiles.models import Profile
from submissions.models import Submission

from ...services import ArxivCaller


class Command(BaseCommand):
    """Update Conflict of Interests using arXiv API."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--arxiv', action='store', default=0, type=str,
            dest='arxiv', help='ArXiv id of Submission to force update of conflicts.')

    def handle(self, *args, **options):
        caller = ArxivCaller()

        if options['arxiv']:
            submissions = Submission.objects.filter(preprint__identifier_w_vn_nr=options['arxiv'])
        else:
            submissions = Submission.objects.needs_conflicts_update()[:5]

        n_new_conflicts = 0
        for sub in submissions:
            fellow_ids = sub.fellows.values_list('id', flat=True)
            fellow_profiles = Profile.objects.filter(contributor__fellowships__id__in=fellow_ids)

            # Get all possibly relevant Profiles
            author_str_list = [a.split()[-1] for a in sub.author_list.split(',')]
            if 'entries' in sub.metadata:
                sub.metadata['entries'][0]['authors']
                # last_names = []
                author_str_list += [
                    a['name'].split()[-1] for a in sub.metadata['entries'][0]['authors']]
                author_str_list = set(author_str_list)  # Distinct operator
            author_profiles = Profile.objects.filter(
                Q(contributor__in=sub.authors.all()) |
                Q(last_name__in=author_str_list)).distinct()

            n_new_conflicts += caller.compare(author_profiles, fellow_profiles, submission=sub)
            Submission.objects.filter(id=sub.id).update(needs_conflicts_update=False)
        return n_new_conflicts
