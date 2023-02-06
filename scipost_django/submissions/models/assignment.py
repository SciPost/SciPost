__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone

from mails.utils import DirectMailUtil

from ..behaviors import SubmissionRelatedObjectMixin
from ..managers import EditorialAssignmentQuerySet


class EditorialAssignment(SubmissionRelatedObjectMixin, models.Model):
    """
    Consideration of a Fellow to become Editor-in-Charge of a Submission.
    """

    REFUSE_OUTSIDE_EXPERTISE = "OFE"
    REFUSE_TOO_BUSY = "BUS"
    REFUSE_ON_VACATION = "VAC"
    REFUSE_COI_COAUTHOR = "COI"
    REFUSE_COI_COLLEAGUE = "CCC"
    REFUSE_COI_COMPETITOR = "CCM"
    REFUSE_COI_OTHER = "COT"
    REFUSE_NOT_IMPARTIAL = "NIR"
    REFUSE_NOT_INTERESTED = "NIE"
    REFUSE_DESK_REJECT = "DNP"
    REFUSAL_REASONS = (
        (REFUSE_OUTSIDE_EXPERTISE, "Outside of my field of expertise"),
        (REFUSE_TOO_BUSY, "Too busy"),
        (REFUSE_ON_VACATION, "Away on vacation"),
        (REFUSE_COI_COAUTHOR, "Conflict of interest: coauthor in last 5 years"),
        (REFUSE_COI_COLLEAGUE, "Conflict of interest: close colleague"),
        (REFUSE_COI_COMPETITOR, "Conflict of interest: close competitor"),
        (REFUSE_COI_OTHER, "Conflict of interest: other"),
        (REFUSE_NOT_IMPARTIAL, "Cannot give an impartial assessment"),
        (REFUSE_NOT_INTERESTED, "Not interested enough"),
        (
            REFUSE_DESK_REJECT,
            "SciPost should desk reject this paper",
        ),
    )

    STATUS_PREASSIGNED = "preassigned"
    STATUS_INVITED = "invited"
    STATUS_ACCEPTED = "accepted"
    STATUS_ACCEPT_IF_NOBODY_ELSE = "accifnobodyelse"
    STATUS_ACCEPT_IF_TRANSFERRED = "acciftransferred"
    STATUS_PERHAPS_LATER = "askagainlater"
    STATUS_DECLINED = "declined"
    STATUS_COMPLETED = "completed"
    STATUS_DEPRECATED = "deprecated"
    STATUS_REPLACED = "replaced"
    ASSIGNMENT_STATUSES = (
        (STATUS_PREASSIGNED, "Preassigned"),
        (STATUS_INVITED, "Invited"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_ACCEPT_IF_NOBODY_ELSE, "Accept (if nobody else does)"),
        (
            STATUS_ACCEPT_IF_TRANSFERRED,
            "Accept (if transferred to non-flagship journal)",
        ),
        (STATUS_PERHAPS_LATER, "Perhaps; ask again later"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_DEPRECATED, "Deprecated"),
        (STATUS_REPLACED, "Replaced"),
    )

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
    )

    to = models.ForeignKey("scipost.Contributor", on_delete=models.CASCADE)

    status = models.CharField(
        max_length=16, choices=ASSIGNMENT_STATUSES, default=STATUS_PREASSIGNED
    )
    refusal_reason = models.CharField(
        max_length=3, choices=REFUSAL_REASONS, blank=True, null=True
    )
    invitation_order = models.PositiveSmallIntegerField(default=0)

    date_created = models.DateTimeField(default=timezone.now)
    date_invited = models.DateTimeField(blank=True, null=True)
    date_answered = models.DateTimeField(blank=True, null=True)

    objects = EditorialAssignmentQuerySet.as_manager()

    class Meta:
        default_related_name = "editorial_assignments"
        ordering = ["-date_created"]

    def __str__(self):
        """Summarize the EditorialAssignment's basic information."""
        return (
            self.to.user.first_name
            + " "
            + self.to.user.last_name
            + " to become EIC of "
            + self.submission.title[:30]
            + " by "
            + self.submission.author_list[:30]
            + ", requested on "
            + self.date_created.strftime("%Y-%m-%d")
        )

    def get_absolute_url(self):
        """Return the url of the assignment's processing page."""
        return reverse("submissions:pool:assignment_request", args=(self.id,))

    @property
    def preassigned(self):
        return self.status == self.STATUS_PREASSIGNED

    @property
    def invited(self):
        return self.status == self.STATUS_INVITED

    @property
    def replaced(self):
        return self.status == self.STATUS_REPLACED

    @property
    def accepted(self):
        return self.status == self.STATUS_ACCEPTED

    @property
    def deprecated(self):
        return self.status == self.STATUS_DEPRECATED

    @property
    def completed(self):
        return self.status == self.STATUS_COMPLETED

    def send_invitation(self):
        """Send invitation and update status."""
        if self.status != self.STATUS_PREASSIGNED:
            # Only send if status is appropriate to prevent double sending
            return False

        # Send mail
        mail_sender = DirectMailUtil(
            mail_code="eic/assignment_request", assignment=self
        )
        mail_sender.send_mail()

        EditorialAssignment.objects.filter(id=self.id).update(
            date_invited=timezone.now(), status=self.STATUS_INVITED
        )

        return True
