__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management import BaseCommand

from ...models import EICRecommendation

from colleges.models import PotentialFellowship
from mails.utils import DirectMailUtil
from colleges.models import Fellowship


class Command(BaseCommand):
    """Send out mail to Fellows letting them know about their open tasks."""

    help = "Sends an email to Fellows with current and upcoming tasks list"

    def handle(self, *args, **kwargs):
        fellowships = Fellowship.objects.active()
        count = 0

        for fellowship in fellowships:
            nr_potfels_to_vote_on = PotentialFellowship.objects.to_vote_on(
                fellowship.contributor
            ).count()
            recs_to_vote_on = EICRecommendation.objects.user_must_vote_on(
                fellowship.contributor.user
            )
            assignments_ongoing = fellowship.contributor.editorial_assignments.ongoing()
            assignments_ongoing_with_required_actions = (
                assignments_ongoing.with_required_actions()
            )
            assignments_to_consider = (
                fellowship.contributor.editorial_assignments.invited()
            )
            assignments_upcoming_deadline = (
                assignments_ongoing.refereeing_deadline_within(days=7)
            )
            if (
                recs_to_vote_on
                or assignments_ongoing_with_required_actions
                or assignments_to_consider
                or assignments_upcoming_deadline
            ):
                mail_sender = DirectMailUtil(
                    "fellows/email_fellow_tasklist",
                    # Render immediately, because m2m/querysets cannot be saved for later rendering:
                    delayed_processing=False,
                    object=fellowship.contributor,
                    fellow=fellowship.contributor,
                    nr_potfels_to_vote_on=nr_potfels_to_vote_on,
                    recs_to_vote_on=recs_to_vote_on,
                    assignments_ongoing=assignments_ongoing,
                    assignments_to_consider=assignments_to_consider,
                    assignments_upcoming_deadline=assignments_upcoming_deadline,
                )
                mail_sender.send_mail()
                count += 1
        self.stdout.write(self.style.SUCCESS("Emailed {} fellows.".format(count)))
