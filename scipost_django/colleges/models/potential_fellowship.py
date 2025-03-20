__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils import timezone

from ..constants import (
    POTENTIAL_FELLOWSHIP_STATUSES,
    POTENTIAL_FELLOWSHIP_IDENTIFIED,
    POTENTIAL_FELLOWSHIP_EVENTS,
)
from ..managers import PotentialFellowshipQuerySet


class PotentialFellowship(models.Model):
    """
    A PotentialFellowship is defined when a researcher has been identified by
    Admin or EdAdmin as a potential member of an Editorial College,
    or when a current Advisory Board member or Fellow nominates the person.

    It is linked to Profile as ForeignKey and not as OneToOne, since the same
    person can eventually be approached on different occasions.

    Using Profile allows to consider both registered Contributors
    and non-registered people.
    """

    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.PROTECT,
        related_name="potential_fellowships",
    )

    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32,
        choices=POTENTIAL_FELLOWSHIP_STATUSES,
        default=POTENTIAL_FELLOWSHIP_IDENTIFIED,
    )
    in_agreement = models.ManyToManyField(
        "scipost.Contributor", related_name="in_agreement_with_election", blank=True
    )
    in_abstain = models.ManyToManyField(
        "scipost.Contributor", related_name="in_abstain_with_election", blank=True
    )
    in_disagreement = models.ManyToManyField(
        "scipost.Contributor", related_name="in_disagreement_with_election", blank=True
    )
    voting_deadline = models.DateTimeField("voting deadline", default=timezone.now)

    objects = PotentialFellowshipQuerySet.as_manager()

    class Meta:
        ordering = ["profile__last_name"]

    def __str__(self):
        return "%s, %s" % (self.profile.__str__(), self.get_status_display())

    def can_vote(self, user):
        """
        Determines whether user can vote on election for this PotentialFellow.
        Qualifying conditions (either of the following):
        * is Admin
        * is in AdvisoryBoard for this College's Academic Field
        * is a Senior Fellow in the College proposed
        """
        return (
            user.contributor.is_scipost_admin
            or user.contributor.is_in_advisory_board
            and user.contributor.profile.acad_field == self.college.acad_field
            or user.contributor.fellowships.senior()
            .filter(college=self.college)
            .exists()
        )

    def latest_event_details(self):
        event = self.potentialfellowshipevent_set.order_by("-noted_on").first()
        if not event:
            return "No event recorded"
        return "%s [%s]" % (
            event.get_event_display(),
            event.noted_on.strftime("%Y-%m-%d"),
        )


class PotentialFellowshipEvent(models.Model):
    """Any event directly related to a PotentialFellowship instance registered as plain text."""

    potfel = models.ForeignKey("colleges.PotentialFellowship", on_delete=models.CASCADE)
    event = models.CharField(max_length=32, choices=POTENTIAL_FELLOWSHIP_EVENTS)
    comments = models.TextField(blank=True)

    noted_on = models.DateTimeField(auto_now_add=True)
    noted_by = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def __str__(self):
        return "%s, %s %s: %s" % (
            self.potfel.profile.last_name,
            self.potfel.profile.get_title_display(),
            self.potfel.profile.first_name,
            self.get_event_display(),
        )
