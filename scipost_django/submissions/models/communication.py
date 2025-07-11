__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone

from common.utils.models import get_current_domain
from mails.utils import DirectMailUtil

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import ED_COMM_CHOICES, ED_COMM_PARTIES
from ..managers import EditorialCommunicationQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from profiles.models import Profile
    from submissions.models import Submission


class EditorialCommunication(SubmissionRelatedObjectMixin, models.Model):
    """Message between two of the EIC, referees, Editorial Administration and/or authors."""

    submission = models.ForeignKey["Submission"](
        "submissions.Submission", on_delete=models.CASCADE
    )
    referee = models.ForeignKey["Profile"](
        "profiles.Profile", on_delete=models.CASCADE, blank=True, null=True
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
            output += " " + self.referee.full_name
        output += " for submission {title} by {authors}".format(
            title=self.submission.title[:30], authors=self.submission.author_list[:30]
        )
        return output

    def get_absolute_url(self):
        """Return the url of the related Submission detail page."""
        return self.submission.get_absolute_url()

    def get_reply_url(self):
        """Return the url to reply to this communication."""
        return reverse(
            "submissions:communication",
            kwargs={
                "identifier_w_vn_nr": self.submission.preprint.identifier_w_vn_nr,
                "comtype": self.reverse_comtype,
            },
        )

    def _resolve_profile_from_letter(self, letter: str):
        recipients: dict[str, "Profile | None"] = {
            "A": self.submission.submitted_by.profile,
            "R": self.referee,
            "E": self.submission.editor_in_charge.profile
            if self.submission.editor_in_charge
            else None,
        }

        return recipients.get(letter)

    def _resolve_profile_name(self, letter: str):
        if letter == "S":
            return "SciPost Editorial Administration"
        elif letter == "E":
            return "Editor in Charge"
        elif profile := self._resolve_profile_from_letter(letter):
            return profile.formal_name
        return "Unknown"

    def _resolve_profile_email(self, letter: str):
        if letter == "S":
            domain = get_current_domain()
            return f"submissions@{domain}"
        elif letter == "R" and self.referee:
            # Attempt to get the referee's email through the invitation
            if ref_invitation := self.submission.referee_invitations.filter(
                referee=self.referee,
                cancelled=False,
            ).first():
                return ref_invitation.email_address

        # In the generic case, resolve Contributor and use Profile's primary
        if profile := self._resolve_profile_from_letter(letter):
            return profile.email
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
        return self._resolve_profile_from_letter(self.author_letter)

    @property
    def recipient(self):
        return self._resolve_profile_from_letter(self.recipient_letter)

    @property
    def author_name(self):
        return self._resolve_profile_name(self.author_letter)

    @property
    def recipient_name(self):
        return self._resolve_profile_name(self.recipient_letter)

    @property
    def author_email(self):
        return self._resolve_profile_email(self.author_letter)

    @property
    def recipient_email(self):
        return self._resolve_profile_email(self.recipient_letter)

    @property
    def reverse_comtype(self):
        """Return the reverse communication type, e.g. EtoA -> AtoE."""
        return self.recipient_letter + "to" + self.author_letter

    def send_email(self):
        valid_comtypes = [comtype[0] for comtype in ED_COMM_CHOICES]
        valid_comtypes.remove("RtoA")  # Referee to Author communication is forbidden
        valid_comtypes.remove("AtoR")  # Author to Referee communication is forbidden

        if self.comtype not in valid_comtypes:
            raise ValueError(
                f"Invalid comtype {self.comtype}. Valid comtypes are {valid_comtypes}."
            )

        DirectMailUtil(
            "submissions/editorial_communication_notification",
            {"communication": self, "domain": get_current_domain()},
        ).send_mail()
