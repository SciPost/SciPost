__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import traceback

from django.core.management.base import BaseCommand

from submissions.models import Submission


class Command(BaseCommand):
    """Verify the metadata formatting and flag errors."""

    def handle(self, *args, **kwargs):
        for sub in Submission.objects.all():
            # Check that the author list is properly formatted
            try:
                if 'entries' in sub.metadata:
                    author_str_list = [
                        a['name'].split()[-1] for a in sub.metadata['entries'][0]['authors']]
            except:
                print('Error for %s' % sub.preprint)
                traceback.print_exc()
