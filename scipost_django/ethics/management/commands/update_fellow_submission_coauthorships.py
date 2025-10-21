__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.core.management.base import BaseCommand
from ethics.tasks import (
    celery_fetch_potential_coauthorships_for_profile_and_submission_authors,
)
from submissions.models import Submission


class Command(BaseCommand):
    """Compare submission fellows and authors for potential coauthorships."""

    def handle(self, *args, **options):
        submissions: list[Submission] = list(
            Submission.objects.all()
            .stage_preassignment_completed()
            .needs_coauthorships_update()
            .prefetch_related("fellows")[:1]
        )

        for submission in submissions:
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
