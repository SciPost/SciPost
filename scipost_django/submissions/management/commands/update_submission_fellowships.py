__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from ...models import Submission
import logging


class Command(BaseCommand):
    help = "Update the fellowships of submissions without EiC assignment."

    def handle(self, *args, **kwargs):
        fellowship_updates_logger = logging.getLogger("submissions.fellowships.update")

        status_no_eic = [
            Submission.INCOMING,
            Submission.ADMISSIBLE,
            Submission.PREASSIGNMENT,
            Submission.SEEKING_ASSIGNMENT,
        ]

        for submission in Submission.objects.filter(status__in=status_no_eic):
            old_fellowship = set(submission.fellows.all())
            new_fellowship = set(submission.get_default_fellowship())

            to_add_fellows = new_fellowship - old_fellowship

            if len(to_add_fellows) == 0:
                continue

            # Only add fellowships and not remove them
            submission.fellows.add(*to_add_fellows)

            update_msg = (
                "Updated the fellowships of {submission} with: {added_fellows}".format(
                    submission=submission.preprint.identifier_w_vn_nr,
                    added_fellows=", ".join(
                        map(
                            lambda f: f.contributor.user.get_full_name(),
                            to_add_fellows,
                        )
                    ),
                )
            )

            fellowship_updates_logger.info(update_msg)
            self.stdout.write(self.style.SUCCESS(update_msg))
