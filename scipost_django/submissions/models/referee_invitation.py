__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from django.utils import timezone

from scipost.constants import TITLE_CHOICES

from ..behaviors import SubmissionRelatedObjectMixin
from ..managers import RefereeInvitationQuerySet
from ..models import EditorialAssignment

if TYPE_CHECKING:
    from profiles.models import Profile
    from scipost.models import Contributor
    from submissions.models import Submission


class RefereeInvitation(SubmissionRelatedObjectMixin, models.Model):
    """Invitation to an active professional scientist to referee a Submission.

    A RefereeInvitation represents an invitation to a Contributor
    or a non-registered scientist to write a Report for a specific Submission.
    The instance will register the response to the invitation and
    the current status of the refereeing duty if the invitation has been accepted.

    """

    profile = models.ForeignKey["Profile"](
        "profiles.Profile", on_delete=models.SET_NULL, blank=True, null=True
    )
    submission = models.ForeignKey["Submission"](
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="referee_invitations",
    )
    referee = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        related_name="referee_invitations",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email_address = models.EmailField()

    # if Contributor not found, person is invited to register
    invitation_key = models.CharField(max_length=40, blank=True)
    date_invited = models.DateTimeField(blank=True, null=True)
    invited_by = models.ForeignKey(
        "scipost.Contributor",
        related_name="referee_invited_by",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    auto_reminders_allowed = models.BooleanField(default=True)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    accepted = models.BooleanField(
        blank=True,
        null=True,
        choices=((None, "Response pending"), (True, "Accept"), (False, "Decline")),
        default=None,
    )
    date_responded = models.DateTimeField(blank=True, null=True)
    refusal_reason = models.CharField(
        max_length=3,
        choices=EditorialAssignment.REFUSAL_REASONS,
        blank=True,
        null=True,
    )
    other_refusal_reason = models.CharField(max_length=255, blank=True, null=True)
    fulfilled = models.BooleanField(
        default=False
    )  # True if a Report has been submitted
    cancelled = models.BooleanField(
        default=False
    )  # True if EIC has deactivated invitation

    objects = RefereeInvitationQuerySet.as_manager()

    class Meta:
        ordering = [
            "-date_invited",
        ]

    def __str__(self):
        """Summarize the RefereeInvitation's basic information."""
        value = (
            self.referee_str
            + " to referee "
            + self.submission.title[:30]
            + " by "
            + self.submission.author_list[:30]
        )
        if self.date_invited:
            value += ", invited on " + self.date_invited.strftime("%Y-%m-%d")
        else:
            value += ", NO EMAIL SENT YET"
        return value

    def get_absolute_url(self):
        """Return url of the invitation's processing page."""
        return reverse("submissions:accept_or_decline_ref_invitations", args=(self.id,))

    @property
    def referee_str(self):
        """Return the most up-to-date name of the Referee."""
        if self.referee:
            return str(self.referee)
        return self.last_name + ", " + self.first_name

    @property
    def related_report(self):
        """Return the Report that's been created for this invitation."""
        return self.submission.reports.filter(author=self.referee).last()

    @property
    def needs_sending(self):
        """Check if the invitation has been emailed."""
        if not self.date_invited:
            return True
        return False

    @property
    def needs_response(self):
        """Check if invitation has no response in more than three days."""
        if not self.cancelled and self.accepted is None:
            if self.date_last_reminded:
                # No reponse in over three days since last reminder
                return timezone.now() - self.date_last_reminded > datetime.timedelta(
                    days=3
                )

            # No reponse in over three days since original invite
            if not self.date_invited:
                return True
            else:
                return timezone.now() - self.date_invited > datetime.timedelta(days=3)

        return False

    @property
    def needs_fulfillment_reminder(self):
        """Check if isn't fullfilled but deadline is closing in."""
        if self.accepted and not self.cancelled and not self.fulfilled:
            # Refereeing deadline closing in/overdue, but invitation isn't fulfilled yet.
            return (self.submission.reporting_deadline - timezone.now()).days < 7
        return False

    @property
    def is_overdue(self):
        """Check if isn't fullfilled but deadline has expired."""
        if self.accepted and not self.cancelled and not self.fulfilled:
            # Refereeing deadline closing in/overdue, but invitation isn't fulfilled yet.
            return (self.submission.reporting_deadline - timezone.now()).days < 0
        return False

    @property
    def needs_attention(self):
        """Check if invitation needs attention by the editor."""
        return (
            self.needs_sending or self.needs_response or self.needs_fulfillment_reminder
        )

    @property
    def get_status_display(self):
        """Get status: a combination between different boolean fields."""
        if self.cancelled:
            return "Cancelled"
        if self.fulfilled:
            return "Fulfilled"
        if self.accepted is None:
            return "Awaiting response"
        elif self.accepted:
            return "Accepted"
        else:
            return "Declined ({})".format(self.get_refusal_reason_display())

    def reset_content(self):
        """Reset the invitation's information as a new invitation."""
        self.nr_reminders = 0
        self.date_last_reminded = None
        self.accepted = None
        self.refusal_reason = None
        self.fulfilled = False
        self.cancelled = False
