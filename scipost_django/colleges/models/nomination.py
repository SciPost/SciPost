__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone

from ..permissions import is_edadmin
from ..managers import (
    FellowshipNominationQuerySet,
    FellowshipNominationVotingRoundQuerySet,
    FellowshipNominationVoteQuerySet,
)

from scipost.models import get_sentinel_user

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from colleges.models import College, Fellowship
    from profiles.models import Profile
    from scipost.models import Contributor


class FellowshipNomination(models.Model):
    voting_rounds: "RelatedManager[FellowshipNominationVotingRound]"
    events: "RelatedManager[FellowshipNominationEvent]"
    invitation: "FellowshipInvitation | None"

    college_id: int
    college = models.ForeignKey["College"](
        "colleges.College", on_delete=models.PROTECT, related_name="nominations"
    )

    profile_id: int
    profile = models.ForeignKey["Profile"](
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="fellowship_nominations",
    )

    nominated_by_id: int
    nominated_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="fellowship_nominations_initiated",
    )

    nominated_on = models.DateTimeField(default=timezone.now)

    nominator_comments = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
        blank=True,
    )

    # vetoes collected by other fellows
    vetoes = models.ManyToManyField["FellowshipNomination", "Fellowship"](
        "colleges.Fellowship",
        related_name="nominations_vetoed",
        blank=True,
    )

    # if elected and invitation accepted, link to Fellowship
    fellowship = models.OneToOneField["Fellowship"](
        "colleges.Fellowship",
        on_delete=models.CASCADE,
        related_name="nomination",
        blank=True,
        null=True,
    )

    objects = FellowshipNominationQuerySet.as_manager()

    class Meta:
        ordering = [
            "profile",
            "college",
        ]
        verbose_name_plural = "Fellowship Nominations"

    def __str__(self):
        return (
            f"{self.profile} to {self.college} "
            f'on {self.nominated_on.strftime("%Y-%m-%d")}'
        )

    def add_event(
        self,
        description: str = "",
        by: "Contributor | None" = None,
    ):
        event = FellowshipNominationEvent(
            nomination=self,
            description=description,
            by=by,
        )
        event.save()

    @property
    def ongoing_voting_round(self):
        return self.voting_rounds.ongoing().first()

    @property
    def latest_voting_round(self):
        return self.voting_rounds.first()

    @property
    def decision(self):
        """The singular non-deprecated decision for this nomination."""
        return self.latest_voting_round.decision

    @property
    def decision_blocks(self):
        """
        List of blocking facts (if any) preventing fixing a decision.
        """
        if latest_round := self.latest_voting_round:
            eligible_count = latest_round.eligible_to_vote.count()
            if eligible_count < 3:
                return "Fewer than 3 eligible voters (insufficient)."
            votes_count = latest_round.votes.count()
            if (
                eligible_count == votes_count  # everybody (>=3) has voted
                or latest_round.voting_deadline
                and latest_round.voting_deadline < timezone.now()
            ):
                return None
            return "Latest voting round is ongoing, and not everybody has voted."
        return "No voting round found."

    # FIX: This is wrong semantically...
    @property
    def get_eligible_voters(self):
        specialties_slug_list = [s.slug for s in self.profile.specialties.all()]

        eligible_voters = (
            Fellowship.objects.active()
            .senior()
            .specialties_overlap(specialties_slug_list)
            .distinct()
        )

        return eligible_voters

    @property
    def edadmin_notes(self):
        """Notes to be displayed to edadmin on the nomination page."""
        notes: list[tuple[str, str]] = []

        try:
            if self.invitation is None:
                return notes
        except FellowshipInvitation.DoesNotExist:
            return notes

        if self.invitation.accepted:
            if not hasattr(self.profile, "contributor"):
                notes.append(
                    (
                        "info",
                        "Fellow has accepted their invitation, but has not registered yet.",
                    )
                )
            elif getattr(self, "fellowship") is None:
                notes.append(
                    (
                        "warning",
                        "Fellow has created an account, but their Fellowship has not been created yet.",
                    )
                )

        last_reinvited = self.events.filter(
            Q(description__icontains="invitation reminder")
            | Q(description__icontains="invitation email")
        ).first()
        two_weeks_ago = timezone.now() - timezone.timedelta(days=14)
        need_reminder_responses = [
            FellowshipInvitation.RESPONSE_INVITED,
            FellowshipInvitation.RESPONSE_REINVITED,
            FellowshipInvitation.RESPONSE_MULTIPLY_REINVITED,
        ]
        if (
            (self.invitation.response in need_reminder_responses)
            and last_reinvited
            and (last_reinvited.on < two_weeks_ago)
        ):
            notes.append(
                (
                    "warning",
                    "Last invitation reminder sent more than two weeks ago.",
                )
            )

        in_one_week = timezone.now() + timezone.timedelta(days=7)
        if (
            self.invitation.postponement_date is not None
            and self.invitation.postponement_date < in_one_week.date()
        ):
            if self.invitation.response == FellowshipInvitation.RESPONSE_POSTPONED:
                notes.append(
                    (
                        "warning",
                        "Postponed start date is less than one week away.",
                    )
                )
            elif (
                self.invitation.response == FellowshipInvitation.RESPONSE_REINVITE_LATER
            ):
                notes.append(
                    (
                        "warning",
                        "Date to reinvite the fellow is less than one week away.",
                    )
                )

        return notes


class FellowshipNominationEvent(models.Model):
    nomination_id: int
    nomination = models.ForeignKey["FellowshipNomination"](
        "colleges.FellowshipNomination",
        on_delete=models.CASCADE,
        related_name="events",
    )

    description = models.TextField()
    on = models.DateTimeField(default=timezone.now)

    by_id: int
    by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.SET(get_sentinel_user),
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["nomination", "-on"]
        verbose_name_plural = "Fellowhip Nomination Events"
        get_latest_by = "on"

    def __str__(self):
        return (
            f"Event for {self.nomination.profile} by {self.by} on {self.on}: "
            f"{self.description}"
        )


class FellowshipNominationComment(models.Model):
    nomination_id: int
    nomination = models.ForeignKey["FellowshipNomination"](
        "colleges.FellowshipNomination",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    by_id: int
    by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
    )

    text = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        )
    )

    on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-on"]
        verbose_name_plural = "Fellowhip Nomination Comments"

    def __str__(self):
        return f"Comment on {self.nomination}"


class FellowshipNominationVotingRound(models.Model):
    TYPE_SENIOR = "senior"
    TYPE_REGULAR = "regular"
    VOTING_ROUND_TYPES = [
        (TYPE_SENIOR, "Senior"),
        (TYPE_REGULAR, "Regular"),
    ]

    votes: "RelatedManager[FellowshipNominationVote]"

    nomination_id: int
    nomination = models.ForeignKey["FellowshipNomination"](
        "colleges.FellowshipNomination",
        on_delete=models.CASCADE,
        related_name="voting_rounds",
    )

    eligible_to_vote = models.ManyToManyField[
        "FellowshipNominationVotingRound", "Fellowship"
    ](
        "colleges.Fellowship",
        related_name="voting_rounds_eligible_to_vote_in",
        blank=True,
    )

    type = models.CharField(
        max_length=16, choices=VOTING_ROUND_TYPES, default=TYPE_SENIOR
    )

    voting_opens = models.DateTimeField(blank=True, null=True)
    voting_deadline = models.DateTimeField(blank=True, null=True)

    objects = FellowshipNominationVotingRoundQuerySet.as_manager()

    class Meta:
        ordering = [
            "nomination__profile__last_name",
            "-voting_deadline",
        ]
        verbose_name_plural = "Fellowship Nomination Voting Rounds"

    def __str__(self):
        if self.voting_deadline is None or self.voting_opens is None:
            return f"Unscheduled voting round for {self.nomination}"
        return (
            f'Voting round ({self.voting_opens.strftime("%Y-%m-%d")} -'
            f' {self.voting_deadline.strftime("%Y-%m-%d")}) for {self.nomination}'
        )

    def vote_of_Fellow(self, fellow):
        fellow_vote = self.votes.filter(fellow=fellow).first()
        return fellow_vote.vote if fellow_vote else None

    def add_voter(self, fellow: "Fellowship"):
        self.eligible_to_vote.add(fellow)
        self.save()

    @property
    def is_open(self):
        if (self.voting_deadline is None) or (self.voting_opens is None):
            return False
        return self.voting_opens <= timezone.now() <= self.voting_deadline

    @property
    def is_scheduled(self):
        return (self.voting_opens is not None) and (self.voting_opens > timezone.now())

    @property
    def is_unscheduled(self):
        return (self.voting_opens is None) or (self.voting_deadline is None)

    @property
    def is_closed(self):
        return (self.voting_deadline is not None) and (
            self.voting_deadline < timezone.now()
        )

    @property
    def vote_outcome(self):
        """The outcome as determined by the votes."""
        if self.nomination.vetoes.all():
            return FellowshipNominationDecision.OUTCOME_NOT_ELECTED

        nr_votes_agree = self.votes.agree().count()
        nr_votes_disagree = self.votes.disagree().count()
        nr_non_abstaining_votes = nr_votes_agree + nr_votes_disagree

        # Guard division by zero
        if nr_non_abstaining_votes == 0:
            return FellowshipNominationDecision.OUTCOME_NOT_ELECTED

        # By-laws 1.3.4 grand fellowship if there is a majority of non-abstaining votes.
        # Agree is counted as +1, disagree as -1
        agree_ratio = (nr_votes_agree - nr_votes_disagree) / nr_non_abstaining_votes
        if agree_ratio >= 0.5:
            return FellowshipNominationDecision.OUTCOME_ELECTED
        else:
            return FellowshipNominationDecision.OUTCOME_NOT_ELECTED

    def can_view(self, user: User) -> bool:
        """Return whether the user can view this voting round.
        They must either be edadmin or all of the following:
         - authenticated
         - have voting eligibility in the round."""

        if not user.is_authenticated:
            return False

        if is_edadmin(user):
            return True

        eligibility_per_fellowship = [
            fellowship in self.eligible_to_vote.all()
            for fellowship in user.contributor.fellowships.all()
        ]
        eligible_to_vote = any(eligibility_per_fellowship)

        return eligible_to_vote


class FellowshipNominationVote(models.Model):
    VOTE_AGREE = "agree"
    VOTE_ABSTAIN = "abstain"
    VOTE_DISAGREE = "disagree"
    VOTE_CHOICES = (
        (VOTE_AGREE, "Agree"),
        (VOTE_ABSTAIN, "Abstain"),
        (VOTE_DISAGREE, "Disagree"),
    )
    VOTE_BS_CLASSES = {
        VOTE_AGREE: "success",
        VOTE_ABSTAIN: "warning",
        VOTE_DISAGREE: "danger",
    }

    voting_round_id: int
    voting_round = models.ForeignKey["FellowshipNominationVotingRound"](
        "colleges.FellowshipNominationVotingRound",
        on_delete=models.CASCADE,
        related_name="votes",
    )

    fellow_id: int
    fellow = models.ForeignKey["Fellowship"](
        "colleges.Fellowship",
        on_delete=models.CASCADE,
        related_name="fellowship_nomination_votes",
    )

    vote = models.CharField(max_length=16, choices=VOTE_CHOICES)

    on = models.DateTimeField(blank=True, null=True)

    objects = FellowshipNominationVoteQuerySet.as_manager()

    @property
    def get_vote_bs_class(self):
        return self.VOTE_BS_CLASSES[self.vote]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["voting_round", "fellow"],
                name="unique_together_voting_round_fellow",
            ),
        ]
        ordering = [
            "voting_round",
        ]
        verbose_name_plural = "Fellowship Nomination Votes"


class FellowshipNominationDecision(models.Model):
    voting_round = models.OneToOneField(
        "colleges.FellowshipNominationVotingRound",
        on_delete=models.CASCADE,
        related_name="decision",
        null=True,
        blank=True,
    )

    OUTCOME_ELECTED = "elected"
    OUTCOME_NOT_ELECTED = "notelected"
    OUTCOME_INCONCLUSIVE = "inconclusive"
    OUTCOME_CHOICES = [
        (OUTCOME_ELECTED, "Elected"),
        (OUTCOME_NOT_ELECTED, "Not elected"),
        (OUTCOME_INCONCLUSIVE, "Inconclusive"),
    ]
    outcome = models.CharField(max_length=16, choices=OUTCOME_CHOICES)

    fixed_on = models.DateTimeField(default=timezone.now)

    comments = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
        blank=True,
    )

    class Meta:
        ordering = [
            "voting_round",
        ]
        verbose_name_plural = "Fellowship Nomination Decisions"

    def __str__(self):
        return f"Decision for {self.voting_round}: {self.get_outcome_display()}"

    @property
    def elected(self):
        return self.outcome == self.OUTCOME_ELECTED


class FellowshipInvitation(models.Model):
    nomination = models.OneToOneField["FellowshipNomination"](
        "colleges.FellowshipNomination",
        on_delete=models.CASCADE,
        related_name="invitation",
    )

    invited_on = models.DateTimeField(blank=True, null=True)

    RESPONSE_NOT_YET_INVITED = "notyetinvited"
    RESPONSE_INVITED = "invited"
    RESPONSE_REINVITED = "reinvited"
    RESPONSE_MULTIPLY_REINVITED = "multireinvited"
    RESPONSE_UNRESPONSIVE = "unresponsive"
    RESPONSE_REINVITE_LATER = "reinvitelater"
    RESPONSE_ACCEPTED = "accepted"
    RESPONSE_POSTPONED = "postponed"
    RESPONSE_DECLINED = "declined"
    RESPONSE_CHOICES = [
        (RESPONSE_NOT_YET_INVITED, "Not yet invited"),
        (RESPONSE_INVITED, "Invited"),
        (RESPONSE_REINVITED, "Reinvited"),
        (RESPONSE_MULTIPLY_REINVITED, "Multiply reinvited"),
        (RESPONSE_UNRESPONSIVE, "Unresponsive"),
        (RESPONSE_REINVITE_LATER, "Reinvite later"),
        (RESPONSE_ACCEPTED, "Accepted, for immediate start"),
        (RESPONSE_POSTPONED, "Accepted, but start date postponed"),
        (RESPONSE_DECLINED, "Declined"),
    ]
    response = models.CharField(max_length=16, choices=RESPONSE_CHOICES, blank=True)

    postponement_date = models.DateField(blank=True, null=True)

    comments = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
        blank=True,
    )

    class Meta:
        ordering = [
            "nomination",
        ]
        verbose_name_plural = "Fellowship Invitations"

    def __str__(self):
        return f"Invitation for {self.nomination}"

    @property
    def accepted(self):
        return self.response in [self.RESPONSE_ACCEPTED, self.RESPONSE_POSTPONED]

    @property
    def declined(self):
        return self.response == self.RESPONSE_DECLINED

    @property
    def in_final_state(self):
        return self.response in [
            self.RESPONSE_ACCEPTED,
            self.RESPONSE_DECLINED,
            self.RESPONSE_POSTPONED,
            self.RESPONSE_UNRESPONSIVE,
        ]

    @property
    def get_response_color(self):
        if self.response in [self.RESPONSE_ACCEPTED, self.RESPONSE_POSTPONED]:
            return "success"
        elif self.response in [self.RESPONSE_DECLINED, self.RESPONSE_NOT_YET_INVITED]:
            return "danger"
        elif self.response in [self.RESPONSE_UNRESPONSIVE]:
            return "warning"
        else:
            return "primary"
