__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.db.models import Q

from submissions.constants import STATUS_FAILED_UPLOAD, STATUS_SENT, STATUS_WAITING
from submissions.models.submission import Submission
from submissions.tasks import create_iThenticate_submission, request_iThenticate_report


class Command(BaseCommand):
    help = "Executes Celery tasks to run iThenticate plagiarism checks for all submissions not fully processed."
    BASE_COUNTDOWN = 6  # seconds
    MAX_TO_PROCESS = 1  # maximum number of submissions to process in one run

    def handle(self, *args, **options):
        submissions = (
            Submission.objects.filter(
                status__in=Submission.STAGE_INCOMING + Submission.STAGE_PREASSIGNMENT
            )
            .order_by("submission_date")
            .select_related("iThenticate_plagiarism_report")
        )

        not_uploaded = submissions.filter(
            Q(iThenticate_plagiarism_report__isnull=True)
            | Q(
                iThenticate_plagiarism_report__status__in=[
                    STATUS_WAITING,
                    STATUS_FAILED_UPLOAD,
                ]
            )
        )
        for i, submission in enumerate(not_uploaded[: self.MAX_TO_PROCESS]):
            create_iThenticate_submission.apply_async(
                (submission.id,), countdown=self.BASE_COUNTDOWN * i
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Creating iThenticate submission for SciPost Submission {submission.id}"
                )
            )

        not_generated = submissions.filter(
            iThenticate_plagiarism_report__status=STATUS_SENT
        )
        for i, submission in enumerate(not_generated[: self.MAX_TO_PROCESS]):
            request_iThenticate_report.apply_async(
                (submission.id,),
                countdown=self.BASE_COUNTDOWN * i + self.BASE_COUNTDOWN // 2,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Requesting iThenticate report for SciPost Submission {submission.id}"
                )
            )
