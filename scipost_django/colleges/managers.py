__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Q, Prefetch
from django.utils import timezone

from .constants import POTENTIAL_FELLOWSHIP_ELECTION_VOTE_ONGOING


class FellowQuerySet(models.QuerySet):
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

    def ordered(self):
        """Return ordered queryset explicitly, since this may have big effect on performance."""
        return self.order_by("contributor__user__last_name")

    def return_active_for_submission(self, submission):
        """
        This method returns a *list* of Fellowships that passed the 'author-check' for
        a specific submission.
        """
        try:
            qs = self.exclude(contributor__in=submission.authors.all()).active()
            false_claims = submission.authors_false_claims.all()
            author_list = submission.author_list.lower()
            fellowships = []
            for fellowship in qs:
                if (
                    fellowship.contributor.user.last_name.lower() in author_list
                    and fellowship.contributor not in false_claims
                ):
                    continue
                fellowships.append(fellowship)
            return fellowships
        except AttributeError:
            return []

    def no_competing_interests_with(self, profile):
        """
        Returns all Fellowships whose profiles have no competing interests with the specified profile.
        """
        from ethics.models import CompetingInterest

        profile_CI, related_CI = CompetingInterest.objects.filter(
            Q(profile=profile) | Q(related_profile=profile)
        ).values_list("profile", "related_profile")

        return self.exclude(
            contributor__profile__pk__in=profile_CI + related_CI,
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
        # votable_rounds = self.voting_rounds.where_user_can_vote(user)
        return self.filter(
            Q(voting_rounds__eligible_to_vote__in=user.contributor.fellowships.active())
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

    def veto(self):
        return self.filter(vote=self.model.VOTE_VETO)
