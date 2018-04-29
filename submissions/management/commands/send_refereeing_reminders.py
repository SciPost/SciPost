__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.utils import timezone

from common.utils import workdays_between
from mails.utils import DirectMailUtil

from ...models import Submission


class Command(BaseCommand):
    help = 'Sends all email reminders needed for Submissions undergoing refereeing'

    def handle(self, *args, **options):
        for submission in Submission.objects.open_for_reporting():
            # Send reminders to referees who have not responded:
            for invitation in submission.referee_invitations.pending():
                # 2 days after ref invite sent out: first auto reminder
                if workdays_between(invitation.date_invited, timezone.now()) == 2:
                    if invitation.referee:
                        mail_sender = DirectMailUtil(
                            mail_code='referees/invite_contributor_to_referee_reminder1',
                            instance=invitation)
                        mail_sender.send()
                    else:
                        mail_sender = DirectMailUtil(
                            mail_code='referees/invite_unregistered_to_referee_reminder1',
                            instance=invitation)
                        mail_sender.send()
                    invitation.nr_reminders += 1
                    invitation.date_last_reminded = timezone.now()
                    invitation.save()
                # second (and final) reminder after 4 days
                elif workdays_between(invitation.date_invited, timezone.now()) == 4:
                    if invitation.referee:
                        mail_sender = DirectMailUtil(
                            mail_code='referees/invite_contributor_to_referee_reminder2',
                            instance=invitation)
                        mail_sender.send()
                    else:
                        mail_sender = DirectMailUtil(
                            mail_code='referees/invite_unregistered_to_referee_reminder2',
                            instance=invitation)
                        mail_sender.send()
                    invitation.nr_reminders += 1
                    invitation.date_last_reminded = timezone.now()
                    invitation.save()
                # after 6 days of no response, EIC is automatically emailed
                # with the suggestion of removing and replacing this referee
                elif workdays_between(invitation.date_invited, timezone.now()) == 6:
                    mail_sender = DirectMailUtil(
                        mail_code='eic/referee_unresponsive', instance=invitation)
                    mail_sender.send()
            # one week before refereeing deadline: auto email reminder to ref
            if workdays_between(timezone.now(), submission.reporting_deadline) == 5:
                for invitation in submission.refereeing_invitations.in_process():
                    mail_sender = DirectMailUtil(
                        mail_code='referees/remind_referee_deadline_1week', instance=invitation)
                    mail_sender.send()
