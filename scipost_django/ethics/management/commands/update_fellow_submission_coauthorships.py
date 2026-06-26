__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.core.management.base import BaseCommand
from ethics.tasks import query_submission_authors_fellows_coauthorships
from submissions.models import Submission

from django_celery_results.models import TaskResult

class Command(BaseCommand):
    """Compare submission fellows and authors for potential coauthorships."""

    SUBMISSIONS_PROCESSED_PER_RUN = 1

    def handle(self, *args, **options):

        scheduled_coauthorship_tasks = TaskResult.objects.filter(
            task_name="ethics.tasks.task_query_coauthorships_in_server",
            status__in=["STARTED", "PENDING"],
        )
        if scheduled_coauthorship_tasks.exists():
            self.stdout.write(
                self.style.WARNING(
                    "There are already scheduled coauthorship-fetching tasks. "
                    "Please wait for them to finish before scheduling new ones."
                )
            )
            return

        submissions: list[Submission] = list(
            Submission.objects.all()
            .stage_incoming_completed()
            .filter(
                coauthorships_update_status__in=[
                    Submission.COAUTHORSHIPS_UNKNOWN,
                    Submission.COAUTHORSHIPS_FAILED,
                ]
            )
            .prefetch_related("fellows")
            .order_by("-coauthorships_update_status", "latest_activity")
        )

        submissions_processed = 0
        for submission in submissions:
            if submissions_processed >= self.SUBMISSIONS_PROCESSED_PER_RUN:
                break

            if not submission.enough_author_profiles_matched:
                continue

            # Schedule the task to query coauthorships for this submission
            # This is a celery chord, and will handle success and failure on its own.
            query_submission_authors_fellows_coauthorships(submission.id).apply_async()

            submission.coauthorships_update_status = Submission.COAUTHORSHIPS_FETCHING
            submission.save()

            submissions_processed += 1
