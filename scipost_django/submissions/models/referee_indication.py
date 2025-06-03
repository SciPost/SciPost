__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from typing import TYPE_CHECKING, Literal
from django.db import models

from colleges.permissions import is_edadmin
from submissions.managers.referee_indication import RefereeIndicationQuerySet

if TYPE_CHECKING:
    from .submission import Submission
    from ...profiles.models import Profile


class RefereeIndication(models.Model):
    """
    Indication of a professional scientist to referee a Submission.

    The indication may not always be positive, i.e. to suggest a scientist
    but also to suggest *not* to invite a scientist to referee a Submission.

    The indication must refer to either an existing Profile or a
    collection of `first_name`, `last_name`, `affiliation` and `email_address` fields.
    """

    INDICATION_SUGGEST = "suggest"
    INDICATION_AGAINST = "advise_against"
    INDICATION_CHOICES = [
        (INDICATION_SUGGEST, "Suggest"),
        (INDICATION_AGAINST, "Advise against"),
    ]

    submission = models.ForeignKey["Submission"](
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="referee_indications",
    )
    indicated_by = models.ForeignKey["Profile"](
        "profiles.Profile",
        related_name="referee_indications_made",
        on_delete=models.CASCADE,
    )
    indication = models.CharField(
        max_length=256,
        choices=INDICATION_CHOICES,
    )

    # Preferable to specify an existing Profile if possible
    referee = models.ForeignKey["Profile"](
        "profiles.Profile",
        related_name="referee_indications_received",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    # if Profile does not exist, their details are stored in the following fields
    first_name = models.CharField(max_length=64, blank=True, null=True)
    last_name = models.CharField(max_length=64, blank=True, null=True)
    email_address = models.EmailField(max_length=256, blank=True, null=True)
    affiliation = models.CharField(max_length=256, blank=True, null=True)

    # If the indication is negative, it is best to provide a reason
    reason = models.TextField(blank=True, null=True)

    objects = RefereeIndicationQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "indicated_by", "referee"],
                name="unique_referee_indication",
            )
        ]

    def __str__(self):
        referee_name = (
            self.referee.full_name
            if self.referee
            else f"{self.first_name} {self.last_name}"
        )
        return f"{self.indicated_by.full_name} to {self.get_indication_display().lower()} {referee_name} for {self.submission}"

    @property
    def indicated_by_role(self):
        """
        Return the role of the Profile that made the indication.
        - "editor" if the Profile is the submission's Editor
        - "fellow" if the Profile is a Fellow
        - "author" if the Profile is an Author
        - "referee" if the Profile is another (invited) Referee
        - "edadmin" if the Profile belongs to an Editorial Administrator
        - "contributor" if the Profile is not any of the above
        """
        eic_profile = getattr(self.submission, "editor_in_charge", None)
        user = getattr(self.indicated_by.contributor, "user")
        if self.indicated_by == eic_profile:
            return "editor"
        elif self.indicated_by.id in self.submission.authors.values_list(
            "profile__id", flat=True
        ):
            return "author"
        elif self.indicated_by.id in self.submission.referee_invitations.values_list(
            "referee__id", flat=True
        ):
            return "referee"
        elif self.indicated_by in self.submission.fellows.values_list(
            "contributor__profile__id", flat=True
        ):
            return "fellow"
        elif user and is_edadmin(user):
            return "edadmin"
        else:
            return "contributor"
