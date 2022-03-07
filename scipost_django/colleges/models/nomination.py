__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from ..managers import (
    FellowshipNominationQuerySet,
    FellowshipNominationVotingRoundQuerySet,
    FellowshipNominationVoteQuerySet,
)


class FellowshipNomination(models.Model):

    college = models.ForeignKey(
        "colleges.College", on_delete=models.PROTECT, related_name="nominations"
    )

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="fellowship_nominations",
    )

    nominated_by = models.ForeignKey(
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

    # if elected and invitation accepted, link to Fellowship
    fellowship = models.OneToOneField(
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

    @property
    def ongoing_voting_round(self):
        return self.voting_rounds.ongoing().first()

    @property
    def latest_voting_round(self):
        return self.voting_rounds.first()

    @property
    def decision_blocks(self):
        """
        List of blocking facts (if any) preventing fixing a decision.
        """
        latest_round = self.voting_rounds.first()
        if latest_round:
            eligible_count = latest_round.eligible_to_vote.count()
            if eligible_count < 3:
                return "Fewer than 3 eligible voters (insufficient)."
            votes_count = latest_round.votes.count()
            if (eligible_count == votes_count # everybody (>=3) has voted
                or
                latest_round.voting_deadline < timezone.now()
                ):
                return None
            return "Latest voting round is ongoing, and not everybody has voted."
        return "No voting round found."


class FellowshipNominationComment(models.Model):

    nomination = models.ForeignKey(
        "colleges.FellowshipNomination", on_delete=models.CASCADE, related_name="comments"
    )

    by = models.ForeignKey(
        "scipost.Contributor", on_delete=models.CASCADE,
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


class FellowshipNominationEvent(models.Model):

    nomination = models.ForeignKey(
        "colleges.FellowshipNomination", on_delete=models.CASCADE, related_name="events"
    )

    description = models.TextField()

    on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-on"]
        verbose_name_plural = "Fellowhip Nomination Events"

    def __str__(self):
        return f"Event for {self.nomination}"


class FellowshipNominationVotingRound(models.Model):

    nomination = models.ForeignKey(
        "colleges.FellowshipNomination",
        on_delete=models.CASCADE,
        related_name="voting_rounds",
    )

    eligible_to_vote = models.ManyToManyField(
        "colleges.Fellowship",
        related_name="voting_rounds_eligible_to_vote_in",
        blank=True,
    )

    voting_opens = models.DateTimeField()

    voting_deadline = models.DateTimeField()

    objects = FellowshipNominationVotingRoundQuerySet.as_manager()

    class Meta:
        ordering = [
            "nomination__profile__last_name",
            "-voting_deadline",
        ]
        verbose_name_plural = "Fellowship Nomination Voting Rounds"

    def __str__(self):
        return (
            f'Voting round ({self.voting_opens.strftime("%Y-%m-%d")} -'
            f' {self.voting_deadline.strftime("%Y-%m-%d")}) for {self.nomination}'
        )

    def vote_of_Fellow(self, fellow):
        vote = self.votes.filter(fellow=fellow)
        if vote:
            return vote.vote
        return None


class FellowshipNominationVote(models.Model):

    VOTE_AGREE = "agree"
    VOTE_ABSTAIN = "abstain"
    VOTE_DISAGREE = "disagree"
    VOTE_CHOICES = (
        (VOTE_AGREE, "Agree"),
        (VOTE_ABSTAIN, "Abstain"),
        (VOTE_DISAGREE, "Disagree"),
    )

    voting_round = models.ForeignKey(
        "colleges.FellowshipNominationVotingRound",
        on_delete=models.CASCADE,
        related_name="votes",
    )

    fellow = models.ForeignKey(
        "colleges.Fellowship",
        on_delete=models.CASCADE,
        related_name="fellowship_nomination_votes",
    )

    vote = models.CharField(max_length=16, choices=VOTE_CHOICES)

    on = models.DateTimeField(blank=True, null=True)

    comments = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
        blank=True,
    )

    objects = FellowshipNominationVoteQuerySet.as_manager()

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

    nomination = models.OneToOneField(
        "colleges.FellowshipNomination",
        on_delete=models.CASCADE,
        related_name="decision",
    )

    OUTCOME_ELECTED = "elected"
    OUTCOME_NOT_ELECTED = "notelected"
    OUTCOME_CHOICES = (
        (OUTCOME_ELECTED, "Elected"),
        (OUTCOME_NOT_ELECTED, "Not elected"),
    )
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
            "nomination",
        ]
        verbose_name_plural = "Fellowship Nomination Decisions"

    def __str__(self):
        return f"Decision for {self.nomination}: {self.get_outcome_display()}"

    @property
    def elected(self):
        return self.outcome == self.OUTCOME_ELECTED


class FellowshipInvitation(models.Model):

    nomination = models.OneToOneField(
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
    RESPONSE_ACCEPTED = "accepted"
    RESPONSE_POSTPONED = "postponed"
    RESPONSE_DECLINED = "declined"
    RESPONSE_CHOICES = (
        (RESPONSE_NOT_YET_INVITED, "Not yet invited"),
        (RESPONSE_INVITED, "Invited"),
        (RESPONSE_REINVITED, "Reinvited"),
        (RESPONSE_MULTIPLY_REINVITED, "Multiply reinvited"),
        (RESPONSE_UNRESPONSIVE, "Unresponsive"),
        (RESPONSE_ACCEPTED, "Accepted, for immediate start"),
        (RESPONSE_POSTPONED, "Accepted, but start date postponed"),
        (RESPONSE_DECLINED, "Declined"),
    )
    response = models.CharField(max_length=16, choices=RESPONSE_CHOICES, blank=True)

    postpone_start_to = models.DateField(blank=True)

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
    def declined(self):
        return self.response == self.RESPONSE_DECLINED
