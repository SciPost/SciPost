__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone

from common.utils.models import get_current_domain

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import ED_COMM_CHOICES, ED_COMM_PARTIES
from ..managers import EditorialCommunicationQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scipost.models import Contributor
    from submissions.models import Submission


class EditorialCommunication(SubmissionRelatedObjectMixin, models.Model):
    """Message between two of the EIC, referees, Editorial Administration and/or authors."""

    submission = models.ForeignKey["Submission"](
        "submissions.Submission", on_delete=models.CASCADE
    )
    referee = models.ForeignKey["Contributor"](
        "scipost.Contributor", on_delete=models.CASCADE, blank=True, null=True
    )
    comtype = models.CharField(max_length=4, choices=ED_COMM_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

    objects = EditorialCommunicationQuerySet.as_manager()

    class Meta:
        ordering = ["timestamp"]
        default_related_name = "editorial_communications"

    def __str__(self):
        """Summarize the EditorialCommunication's meta information."""
        output = self.comtype
        if self.referee is not None:
            output += (
                " " + self.referee.user.first_name + " " + self.referee.user.last_name
            )
        output += " for submission {title} by {authors}".format(
            title=self.submission.title[:30], authors=self.submission.author_list[:30]
        )
        return output

    def get_absolute_url(self):
        """Return the url of the related Submission detail page."""
        return self.submission.get_absolute_url()

    def _resolve_contributor_from_letter(self, letter: str):
        recipients: dict[str, "Contributor | None"] = {
            "E": self.submission.editor_in_charge,
            "A": self.submission.submitted_by,
            "R": self.referee,
        }

        return recipients.get(letter)

    def _resolve_contributor_name(self, letter: str):
        if letter == "S":
            return "SciPost Editorial Administration"
        elif letter == "E":
            return "Editor in Charge"
        elif contributor := self._resolve_contributor_from_letter(letter):
            return f"{contributor.profile_title} {contributor.user.last_name}"
        return "Unknown"

    def _resolve_contributor_email(self, letter: str):
        if letter == "S":
            domain = get_current_domain()
            return f"submissions@{domain}"
        elif contributor := self._resolve_contributor_from_letter(letter):
            return contributor.user.email
        return ""

    @property
    def author_letter(self):
        return self.comtype[0]

    @property
    def recipient_letter(self):
        return self.comtype[-1]

    def get_author_type_display(self):
        return dict(ED_COMM_PARTIES).get(self.author_letter, "Unknown")

    def get_recipient_type_display(self):
        return dict(ED_COMM_PARTIES).get(self.recipient_letter, "Unknown")

    @property
    def author(self):
        return self._resolve_contributor_from_letter(self.author_letter)

    @property
    def recipient(self):
        return self._resolve_contributor_from_letter(self.recipient_letter)

    @property
    def author_name(self):
        return self._resolve_contributor_name(self.author_letter)

    @property
    def recipient_name(self):
        return self._resolve_contributor_name(self.recipient_letter)

    @property
    def author_email(self):
        return self._resolve_contributor_email(self.author_letter)

    @property
    def recipient_email(self):
        return self._resolve_contributor_email(self.recipient_letter)
