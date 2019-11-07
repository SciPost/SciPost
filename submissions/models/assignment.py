__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone

from mails.utils import DirectMailUtil

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import (
    ASSIGNMENT_STATUSES, STATUS_PREASSIGNED, STATUS_INVITED, STATUS_REPLACED,
    STATUS_ACCEPTED, STATUS_DEPRECATED, STATUS_COMPLETED,
    ASSIGNMENT_REFUSAL_REASONS)
from ..managers import EditorialAssignmentQuerySet


class EditorialAssignment(SubmissionRelatedObjectMixin, models.Model):
    """Fellow assignment to a Submission to become Editor-in-Charge."""

    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    to = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)

    status = models.CharField(
        max_length=16, choices=ASSIGNMENT_STATUSES, default=STATUS_PREASSIGNED)
    refusal_reason = models.CharField(
        max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS, blank=True, null=True)
    invitation_order = models.PositiveSmallIntegerField(default=0)

    date_created = models.DateTimeField(default=timezone.now)
    date_invited = models.DateTimeField(blank=True, null=True)
    date_answered = models.DateTimeField(blank=True, null=True)

    objects = EditorialAssignmentQuerySet.as_manager()

    class Meta:
        default_related_name = 'editorial_assignments'
        ordering = ['-date_created']

    def __str__(self):
        """Summarize the EditorialAssignment's basic information."""
        return (self.to.user.first_name + ' ' + self.to.user.last_name + ' to become EIC of ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', requested on ' + self.date_created.strftime('%Y-%m-%d'))

    def get_absolute_url(self):
        """Return the url of the assignment's processing page."""
        return reverse('submissions:assignment_request', args=(self.id,))

    @property
    def notification_name(self):
        """Return string representation of this EditorialAssigment as shown in Notifications."""
        return self.submission.preprint.identifier_w_vn_nr

    @property
    def preassigned(self):
        return self.status == STATUS_PREASSIGNED

    @property
    def invited(self):
        return self.status == STATUS_INVITED

    @property
    def replaced(self):
        return self.status == STATUS_REPLACED

    @property
    def accepted(self):
        return self.status == STATUS_ACCEPTED

    @property
    def deprecated(self):
        return self.status == STATUS_DEPRECATED

    @property
    def completed(self):
        return self.status == STATUS_COMPLETED

    def send_invitation(self):
        """Send invitation and update status."""
        if self.status != STATUS_PREASSIGNED:
            # Only send if status is appropriate to prevent double sending
            return False

        # Send mail
        mail_sender = DirectMailUtil(mail_code='eic/assignment_request', assignment=self)
        mail_sender.send_mail()

        EditorialAssignment.objects.filter(
            id=self.id).update(date_invited=timezone.now(), status=STATUS_INVITED)

        return True
