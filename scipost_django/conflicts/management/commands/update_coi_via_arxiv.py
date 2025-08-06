__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from typing import cast

from django.core.management.base import BaseCommand
from django.db.models.manager import BaseManager

from common.utils.text import partial_name_match_regexp
from profiles.models import Profile
from submissions.models import Submission

from ...services import ArxivCaller


class Command(BaseCommand):
    """Update Conflict of Interests using arXiv API."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--arxiv",
            action="store",
            default=0,
            type=str,
            dest="arxiv",
            help="ArXiv id of Submission to force update of conflicts.",
        )

    def handle(self, *args, **options):
        caller = ArxivCaller()

        if identifier := options.get("arxiv"):
            submissions = Submission.objects.filter(
                preprint__identifier_w_vn_nr=identifier
            )
        else:
            submissions = cast(
                BaseManager[Submission], Submission.objects.needs_conflicts_update()[:5]
            )

        n_new_conflicts = 0
        for sub in submissions:
            fellow_ids = sub.fellows.values_list("id", flat=True)
            fellow_profiles = Profile.objects.filter(
                contributor__fellowships__id__in=fellow_ids
            )

            # Get all possibly relevant Profiles
            # Assume the author list is purely comma-separated,
            author_profile_ids: list[int] = []
            for author_name in sub.author_list.split(","):
                author_name_re = partial_name_match_regexp(author_name.strip())
                author_profile_ids += list(
                    Profile.objects.filter(
                        full_name__unaccent__iregex=author_name_re
                    ).values_list("id", flat=True)
                )
            author_profile_ids_set = set(author_profile_ids)
            author_profiles = Profile.objects.filter(pk__in=author_profile_ids_set)

            n_new_conflicts += caller.compare(
                author_profiles, fellow_profiles, submission=sub
            )
            Submission.objects.filter(id=sub.id).update(needs_conflicts_update=False)
        return str(n_new_conflicts)
