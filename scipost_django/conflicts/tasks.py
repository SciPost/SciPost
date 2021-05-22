__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from scipost.models import Contributor
from SciPost_v1.celery import app
from submissions.models import Submission

from .services import ArxivCaller


@app.task(bind=True)
def update_conflict_of_interest(self):
    """Create new Conflict of Interest entries for incoming Submission."""
    submissions = Submission.objects.needs_conflicts_update()
    for sub in submissions:
        fellow_ids = sub.fellows.values_list('id', flat=True)
        fellows = Contributor.objects.filter(fellowships__id__in=fellow_ids)
        if 'entries' in sub.metadata:
            caller = ArxivCaller(sub.metadata['entries'][0]['authors'])
            caller.compare_to(fellows)
            caller.add_to_db(sub)
            Submission.objects.filter(id=sub.id).update(needs_conflicts_update=False)
