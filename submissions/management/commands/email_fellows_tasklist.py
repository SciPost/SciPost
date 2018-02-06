from django.core.management import BaseCommand

from ...models import Submission, EditorialAssignment
from ...utils import SubmissionUtils

from scipost.models import Contributor


class Command(BaseCommand):
    help = 'Sends an email to Fellows with current and upcoming tasks list'
    def handle(self, *args, **kwargs):
        fellows = Contributor.objects.fellows(
        ).filter(user__last_name__startswith='B' # temporary limitation, to ease testing
        ).order_by('user__last_name')

        for fellow in fellows:
            submissions_as_eic = Submission.objects.filter(
                editor_in_charge=fellow).order_by('submission_date')
            assignments_to_consider = EditorialAssignment.objects.open().filter(
                to=fellow)
            if submissions_as_eic or assignments_to_consider:
                SubmissionUtils.load({'fellow': fellow,
                                      'submissions_as_eic': submissions_as_eic,
                                      'assignments_to_consider': assignments_to_consider,})
                SubmissionUtils.email_Fellow_tasklist()
