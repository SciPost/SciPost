__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.utils import timezone

from common.utils import workdays_between
from mails.utils import DirectMailUtil

from ...models import Submission

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...models import RefereeInvitation


class Command(BaseCommand):
    help = "Sends all email reminders needed for Submissions undergoing refereeing"

    def handle(self, *args, **options):
        submission: Submission
        for submission in Submission.objects.open_for_reporting():
            invitations_w_auto_reminders = (
                submission.referee_invitations.auto_reminders_allowed()
            )
            invitation: "RefereeInvitation"

            # Send automatic reminders to referees who have not responded
            for invitation in invitations_w_auto_reminders.awaiting_response():
                referee_registration_status = (
                    "contributor"
                    if invitation.to_registered_referee
                    else "unregistered"
                )

                workdays_since_invitation = (
                    workdays_between(invitation.date_invited, timezone.now())
                    if invitation.date_invited
                    else 0
                )

                # Send the appropriate reminder email based on the number of days since the invitation
                # Subtract 1 from the workday calculation to account for worst case scenario where
                # the reminder email sent in the morning of the workday
                mail = None
                match workdays_since_invitation - 1:
                    case 2:
                        # First reminder according to the referee registration status
                        mail = DirectMailUtil(
                            f"referees/invite_{referee_registration_status}_to_referee_reminder1",
                            invitation=invitation,
                        )
                        invitation.reminder_sent()
                    case 4:
                        # Second reminder according to the referee registration status
                        mail = DirectMailUtil(
                            f"referees/invite_{referee_registration_status}_to_referee_reminder2",
                            invitation=invitation,
                        )
                        invitation.reminder_sent()
                    case 6:
                        # EIC is automatically emailed with the suggestion of removing and replacing this referee
                        mail = DirectMailUtil(
                            "eic/referee_unresponsive", invitation=invitation
                        )

                if mail is not None:
                    mail.send_mail()

            # Send automatic reminder that the deadline is approaching (less than one week left)
            if submission.reporting_deadline is not None:
                workdays_until_deadline = workdays_between(
                    timezone.now(), submission.reporting_deadline
                )
                if workdays_until_deadline == 5:
                    for invitation in invitations_w_auto_reminders.in_process():
                        DirectMailUtil(
                            "referees/remind_referee_deadline_1week",
                            invitation=invitation,
                        ).send_mail()
