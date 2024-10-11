__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.utils import timezone

from mails.utils import DirectMailUtil

from ...models import Submission


class Command(BaseCommand):
    help = "Sends all email reminders needed for Submissions in the assignment stage"

    def handle(self, *args, **options):
        submission: Submission
        for submission in Submission.objects.seeking_assignment():
            now = timezone.now()
            today = now.date()

            # Skip if assignment deadline is not set
            if submission.assignment_deadline is None:
                continue

            # If the date of passing preassignment checks is not set, set it to now
            if submission.checks_cleared_date is None:
                submission.checks_cleared_date = now
                submission.save()

            default_assignment_period_weeks = (
                submission.submitted_to.assignment_period.days // 7
            )

            days_passed = (today - submission.checks_cleared_date.date()).days
            weeks_passed = days_passed // 7

            days_remaining = (submission.assignment_deadline - today).days
            weeks_until_assignment_deadline = days_remaining // 7

            # Send reminders after preassignment checks are cleared and only at 7-day intervals
            if weeks_passed <= 0 or days_passed % 7 != 0:
                continue

            # Send regular reminders if assignment deadline is not passed
            if weeks_until_assignment_deadline > 0:
                mail = DirectMailUtil(
                    f"authors/update_authors_assignment_stage",
                    submission=submission,
                    weeks_passed=weeks_passed,
                    weeks_until_assignment_deadline=weeks_until_assignment_deadline,
                    default_assignment_period_weeks=default_assignment_period_weeks,
                )

            # Automatically fail assignment if the deadline is passed
            else:
                submission.status = Submission.ASSIGNMENT_FAILED
                submission.visible_pool = False
                submission.visible_public = False
                submission.save()

                mail = DirectMailUtil(
                    "authors/submissions_assignment_failed",
                    submission=submission,
                )

            mail.send_mail()
