__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.utils import timezone

from common.utils import workdays_between
from mails.utils import DirectMailUtil

from ...models import Submission


class Command(BaseCommand):
    help = "Sends all email reminders needed for Submissions undergoing refereeing"

    def handle(self, *args, **options):
        for submission in Submission.objects.open_for_reporting():
            # Send reminders to referees who have not responded:
            for (
                invitation
            ) in (
                submission.referee_invitations.awaiting_response().auto_reminders_allowed()
            ):
                # 2 days after ref invite sent out: first auto reminder
                if workdays_between(invitation.date_invited, timezone.now()) == 2:
                    if invitation.referee:
                        mail_sender = DirectMailUtil(
                            "referees/invite_contributor_to_referee_reminder1",
                            invitation=invitation,
                        )
                        mail_sender.send_mail()
                    else:
                        mail_sender = DirectMailUtil(
                            "referees/invite_unregistered_to_referee_reminder1",
                            invitation=invitation,
                        )
                        mail_sender.send_mail()
                    invitation.nr_reminders += 1
                    invitation.date_last_reminded = timezone.now()
                    invitation.save()
                # second (and final) reminder after 4 days
                elif workdays_between(invitation.date_invited, timezone.now()) == 4:
                    if invitation.referee:
                        mail_sender = DirectMailUtil(
                            "referees/invite_contributor_to_referee_reminder2",
                            invitation=invitation,
                        )
                        mail_sender.send_mail()
                    else:
                        mail_sender = DirectMailUtil(
                            "referees/invite_unregistered_to_referee_reminder2",
                            invitation=invitation,
                        )
                        mail_sender.send_mail()
                    invitation.nr_reminders += 1
                    invitation.date_last_reminded = timezone.now()
                    invitation.save()
                # after 6 days of no response, EIC is automatically emailed
                # with the suggestion of removing and replacing this referee
                elif workdays_between(invitation.date_invited, timezone.now()) == 6:
                    mail_sender = DirectMailUtil(
                        "eic/referee_unresponsive", invitation=invitation
                    )
                    mail_sender.send_mail()
            # one week before refereeing deadline: auto email reminder to ref
            if (
                submission.reporting_deadline is not None
                and workdays_between(timezone.now(), submission.reporting_deadline) == 5
            ):
                for (
                    invitation
                ) in (
                    submission.referee_invitations.in_process().auto_reminders_allowed()
                ):
                    mail_sender = DirectMailUtil(
                        "referees/remind_referee_deadline_1week", invitation=invitation
                    )
                    mail_sender.send_mail()
