__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management import BaseCommand

from ...models import Submission, EditorialAssignment
from ...utils import SubmissionUtils

from scipost.models import Contributor


class Command(BaseCommand):
    help = 'Sends an email to Fellows with current and upcoming tasks list'
    def handle(self, *args, **kwargs):
        fellows = Contributor.objects.fellows(
#        ).filter(user__last_name__istartswith='C' # temporary limitation, to ease testing
        ).order_by('user__last_name')

        for fellow in fellows:
            assignments_ongoing = fellow.editorial_assignments.ongoing()
            assignments_to_consider = fellow.editorial_assignments.open()
            assignments_upcoming_deadline = assignments_ongoing.refereeing_deadline_within(days=7)
            if assignments_ongoing or assignments_to_consider or assignments_upcoming_deadline:
                SubmissionUtils.load(
                    {
                        'fellow': fellow,
                        'assignments_ongoing': assignments_ongoing,
                        'assignments_to_consider': assignments_to_consider,
                        'assignments_upcoming_deadline': assignments_upcoming_deadline,
                    }
                )
                SubmissionUtils.email_Fellow_tasklist()
