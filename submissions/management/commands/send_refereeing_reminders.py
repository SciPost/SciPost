__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.utils import timezone

from mails.utils import DirectMailUtil

from ...models import Submission


class Command(BaseCommand):
    help = 'Sends all email reminders needed for Submissions undergoing refereeing'
    def handle(self, *args, **options):
        for submission in Submission.objects.open_for_reporting():
            # fewer than 3 referees invited within 48 hours? EIC must take action
            # TODO
            # 3 days after ref invite sent out, upon no response from referee: first auto reminder
            for invitation in submission.referee_invitations.pending():
                if (timezone.now() > invitation.date_invited + timezone.timedelta(days=2)
                    and timezone.now() < invitation.date_invited + timezone.timedelta(days=3)):
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
            # second and final reminder after 6 days
            # TODO
            # after 8 days of no response, EIC is automatically emailed
            # with the suggestion of removing and replacing this referee
            # TODO
            # one week before refereeing deadline: auto email reminder to ref
            if (submission.reporting_deadline > timezone.now() + timezone.timedelta(days=7)
                and submission.reporting_deadline < timezone.now() + timezone.timedelta(days=8)):
                for invitation in submission.refereeing_invitations.in_process():
                    mail_sender = DirectMailUtil(mail_code='referees/remind_referee_deadline_1week',
                                                 instance=invitation)
                    mail_sender.send()
