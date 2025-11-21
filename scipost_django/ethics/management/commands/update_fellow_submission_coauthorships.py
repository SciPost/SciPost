__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.core.management.base import BaseCommand
from ethics.tasks import (
    celery_fetch_potential_coauthorships_for_profile_and_submission_authors,
)
from submissions.models import Submission


class Command(BaseCommand):
    """Compare submission fellows and authors for potential coauthorships."""

    SUBMISSIONS_PROCESSED_PER_RUN = 1

    def handle(self, *args, **options):
        submissions: list[Submission] = list(
            Submission.objects.all()
            .stage_incoming_completed()
            .needs_coauthorships_update()
            .prefetch_related("fellows")
            .order_by("latest_activity")
        )

        submissions_processed = 0
        for submission in submissions:
            if submissions_processed >= self.SUBMISSIONS_PROCESSED_PER_RUN:
                break

            if not submission.enough_author_profiles_matched:
                continue

            preprint_servers = submission.get_coauthorship_preprint_servers()

            fellow_profile_ids: list[int] = list(
                submission.fellows.all()
                .active()
                .values_list("contributor__profile__id", flat=True)
            )

            for fellow_profile_id in fellow_profile_ids:
                celery_fetch_potential_coauthorships_for_profile_and_submission_authors.delay(
                    fellow_profile_id,
                    submission.id,
                    preprint_servers=preprint_servers,
                )

            submission.needs_coauthorships_update = False
            submission.save()

            submissions_processed += 1
