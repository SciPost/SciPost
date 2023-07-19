__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import (
    Fellowship,
    FellowshipNomination,
    FellowshipNominationVotingRound,
)


class Command(BaseCommand):
    help = "Create voting rounds for nominations requiring handling."

    def handle(self, *args, **kwargs):
        nominations = FellowshipNomination.objects.needing_handling().exclude(
            profile__specialties__isnull=True
        )
        for nomination in nominations:
            specialties_slug_list = [
                s.slug for s in nomination.profile.specialties.all()
            ]
            voting_round = FellowshipNominationVotingRound(
                nomination=nomination,
                voting_opens=timezone.now(),
                voting_deadline=(timezone.now() + datetime.timedelta(days=14)),
            )
            voting_round.save()
            voting_round.eligible_to_vote.set(
                Fellowship.objects.active()
                .senior()
                .specialties_overlap(specialties_slug_list)
            )
            if voting_round.eligible_to_vote.count() <= 5:
                # add Senior Fellows from all specialties
                voting_round.eligible_to_vote.set(
                    Fellowship.objects.active()
                    .senior()
                    .filter(college=nomination.college)
                )
            voting_round.save()

            if voting_round.eligible_to_vote.count() <= 5:
                self.stdout.write(
                    self.style.ERROR(
                        "Only {nr_eligible_voters} eligible voters for {first_name} {last_name}, cannot create round.".format(
                            first_name=nomination.profile.first_name,
                            last_name=nomination.profile.last_name,
                            nr_eligible_voters=voting_round.eligible_to_vote.count(),
                        )
                    )
                )
                voting_round.delete()
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Created voting round for {first_name} {last_name} with {nr_eligible_voters} eligible voters.".format(
                            first_name=nomination.profile.first_name,
                            last_name=nomination.profile.last_name,
                            nr_eligible_voters=voting_round.eligible_to_vote.count(),
                        )
                    )
                )

        if len(nominations) == 0:
            self.stdout.write(
                self.style.ERROR(f"No nominations found needing handling.")
            )
