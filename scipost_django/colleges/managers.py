__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db import models
from django.db.models import F, Q, CharField, Value
from django.utils import timezone
from ethics.models import CompetingInterest
from scipost.models import Contributor

from .constants import POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from colleges.models import Fellowship
    from submissions.models import Submission


class FellowQuerySet(models.QuerySet["Fellowship"]):
    ########################################
    # select_related template accelerators #
    ########################################
    def select_related_contributor__user_and_profile(self):
        return self.select_related(
            "contributor__user",
            "contributor__profile",
        )

    def guests(self):
        from .models import Fellowship

        return self.filter(status=Fellowship.STATUS_GUEST)

    def regular(self):
        from .models import Fellowship

        return self.filter(status=Fellowship.STATUS_REGULAR)

    def senior(self):
        from .models import Fellowship

        return self.filter(status=Fellowship.STATUS_SENIOR)

    def regular_or_senior(self):
        from .models import Fellowship

        return self.filter(
            Q(status=Fellowship.STATUS_REGULAR) | Q(status=Fellowship.STATUS_SENIOR)
        )

    def active(self):
        today = timezone.now().date()
        return self.filter(
            Q(start_date__lte=today, until_date__isnull=True)
            | Q(start_date__isnull=True, until_date__gte=today)
            | Q(start_date__lte=today, until_date__gte=today)
            | Q(start_date__isnull=True, until_date__isnull=True)
        ).ordered()

    def active_in_year(self, year):
        """
        Filter for Fellows which were active during a certain calendar year.
        """
        return self.filter(start_date__year__lte=year, until_date__year__gte=year)

    def former(self):
        today = timezone.now().date()
        return self.filter(until_date__lt=today)

    def specialties_overlap(self, specialties_slug_list):
        """
        Returns all Fellows whose specialties overlap with those specified in the slug list.

        This method is also separately implemented for Contributor and Profile objects.
        """
        return self.filter(
            contributor__profile__specialties__slug__in=specialties_slug_list
        )

    def college_specialties_overlap_with_submission(self, submission: "Submission"):
        """
        Returns all Fellows whose college and specialties overlap with those specified in the submission
        """
        return self.filter(
            college=submission.submitted_to.college,
            contributor__profile__specialties__in=submission.specialties.all(),
        )

    def ordered(self):
        """Return ordered queryset explicitly, since this may have big effect on performance."""
        return self.order_by("contributor__user__last_name")

    def no_competing_interests_with(self, profile):
        """
        Returns all Fellowships whose profiles have no competing interests with the specified profile.
        """
        from profiles.models import Profile

        clear_profiles = Profile.objects.no_competing_interests_with(profile)
        return self.filter(contributor__profile__pk__in=clear_profiles)

    def without_competing_interests_against_submission_authors_of(self, submission):
        """
        Returns all Fellowships whose profiles have no competing interests with any of the authors of the specified submission.
        """
        fellow_profile_ids = self.values_list("contributor__profile", flat=True)
        submission_author_profile_ids = submission.author_profiles.all().values_list(
            "profile_id", flat=True
        )

        fellow_author_cis = CompetingInterest.objects.between_profile_sets(
            fellow_profile_ids, submission_author_profile_ids
        )

        CI_profiles = fellow_author_cis.values_list("profile", "related_profile")
        # Unpack the collection of id-two-tuples into two tuples of ids
        profile_CI, related_CI = tuple(zip(*CI_profiles)) or ((), ())

        return self.exclude(
            contributor__profile__id__in=profile_CI
            + related_CI
            + tuple(submission_author_profile_ids)
        )

    def without_authorship_of_submission(self, submission: "Submission"):
        """
        Exclude all Fellowships which may have authorship with the particular submission:
        - Verified authors
        - Profiles added in preassignment
        - Personal contributor claims of authorship
        """
        preassigned_authors = Contributor.objects.filter(
            profile__in=submission.author_profiles.values("profile")
        )
        submission_authors = submission.authors.all()
        author_claims = submission.authors_claims.all()

        return self.exclude(
            contributor__in=submission_authors | preassigned_authors | author_claims
        )


class PotentialFellowshipQuerySet(models.QuerySet):
    def vote_needed(self, contributor):
        college_id_list = [
            f.college.id for f in contributor.fellowships.senior().active()
        ]
        return (
            self.filter(
                college__pk__in=college_id_list,
                status=POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING,
            )
            .distinct()
            .order_by("profile__last_name")
        )

    def to_vote_on(self, contributor):
        return self.vote_needed(contributor).exclude(
            Q(in_agreement__in=[contributor])
            | Q(in_abstain__in=[contributor])
            | Q(in_disagreement__in=[contributor])
        )

    def voted_on(self, contributor):
        return self.vote_needed(contributor).filter(
            Q(in_agreement__in=[contributor])
            | Q(in_abstain__in=[contributor])
            | Q(in_disagreement__in=[contributor])
        )


class FellowshipNominationQuerySet(models.QuerySet):
    def needing_handling(self):
        return self.exclude(voting_rounds__isnull=False).exclude(
            voting_rounds__decision__isnull=False
        )

    def with_user_votable_rounds(self, user):
        """Return all Fellowship nominations where the user is eligible to vote."""
        return self.filter(
            voting_rounds__eligible_to_vote__in=user.contributor.fellowships.active()
        )


class FellowshipNominationVotingRoundQuerySet(models.QuerySet):
    def ongoing(self):
        now = timezone.now()
        return self.filter(voting_opens__lte=now, voting_deadline__gte=now)

    def closed(self):
        now = timezone.now()
        return self.filter(voting_deadline__lte=now)

    def where_user_can_vote(self, user):
        user_fellowships = user.contributor.fellowships.active()
        return self.filter(eligible_to_vote__in=user_fellowships)


class FellowshipNominationVoteQuerySet(models.QuerySet):
    def agree(self):
        return self.filter(vote=self.model.VOTE_AGREE)

    def abstain(self):
        return self.filter(vote=self.model.VOTE_ABSTAIN)

    def disagree(self):
        return self.filter(vote=self.model.VOTE_DISAGREE)
