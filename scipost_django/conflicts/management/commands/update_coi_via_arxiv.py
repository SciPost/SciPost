__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.db.models import Q

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

        if options["arxiv"]:
            submissions = Submission.objects.filter(
                preprint__identifier_w_vn_nr=options["arxiv"]
            )
        else:
            submissions = Submission.objects.needs_conflicts_update()[:5]

        n_new_conflicts = 0
        for sub in submissions:
            fellow_ids = sub.fellows.values_list("id", flat=True)
            fellow_profiles = Profile.objects.filter(
                contributor__fellowships__id__in=fellow_ids
            )

            # Get all possibly relevant Profiles
            # Assume the author list is purely comma-separated,
            # with entries in format [firstname or initial[.]] lastname
            author_profile_ids = []
            for a in sub.author_list.split(","):
                last = a.split()[-1]
                first = a.split()[0].split(".")[0]
                print("%s %s" % (first, last))
                author_profile_ids += [
                    p.id
                    for p in Profile.objects.filter(
                        last_name__endswith=last, first_name__startswith=first
                    ).all()
                ]
            author_profile_ids_set = set(author_profile_ids)
            author_profiles = Profile.objects.filter(pk__in=author_profile_ids_set)

            n_new_conflicts += caller.compare(
                author_profiles, fellow_profiles, submission=sub
            )
            Submission.objects.filter(id=sub.id).update(needs_conflicts_update=False)
        return str(n_new_conflicts)
