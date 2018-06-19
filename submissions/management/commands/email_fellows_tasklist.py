__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management import BaseCommand

from ...models import Submission, EditorialAssignment, EICRecommendation

from scipost.models import Contributor


class Command(BaseCommand):
    help = 'Sends an email to Fellows with current and upcoming tasks list'
    def handle(self, *args, **kwargs):
        fellows = Contributor.objects.fellows(
        ).order_by('user__last_name')

        for fellow in fellows:
            recs_to_vote_on = EICRecommendation.objects.user_must_vote_on(fellow.user)
            assignments_ongoing = fellow.editorial_assignments.ongoing()
            assignments_to_consider = fellow.editorial_assignments.open()
            assignments_upcoming_deadline = assignments_ongoing.refereeing_deadline_within(days=7)
            if (recs_to_vote_on or assignments_ongoing or
                assignments_to_consider or assignments_upcoming_deadline):
                mail_sender = DirectMailUtil(
                    mail_code='fellows/email_fellow_tasklist',
                    'fellow': fellow,
                    'recs_to_vote_on': recs_to_vote_on,
                    'assignments_ongoing': assignments_ongoing,
                    'assignments_to_consider': assignments_to_consider,
                    'assignments_upcoming_deadline': assignments_upcoming_deadline
                    )
                    mail_sender.send()
