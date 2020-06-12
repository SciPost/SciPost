__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import ED_COMM_CHOICES
from ..managers import EditorialCommunicationQuerySet


class EditorialCommunication(SubmissionRelatedObjectMixin, models.Model):
    """Message between two of the EIC, referees, Editorial Administration and/or authors."""

    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    referee = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                blank=True, null=True)
    comtype = models.CharField(max_length=4, choices=ED_COMM_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

    objects = EditorialCommunicationQuerySet.as_manager()

    class Meta:
        ordering = ['timestamp']
        default_related_name = 'editorial_communications'

    def __str__(self):
        """Summarize the EditorialCommunication's meta information."""
        output = self.comtype
        if self.referee is not None:
            output += ' ' + self.referee.user.first_name + ' ' + self.referee.user.last_name
        output += ' for submission {title} by {authors}'.format(
            title=self.submission.title[:30],
            authors=self.submission.author_list[:30])
        return output

    def get_absolute_url(self):
        """Return the url of the related Submission detail page."""
        return self.submission.get_absolute_url()

    def get_notification_url(self, url_code):
        """Return url related to the Communication by the `url_code` meant for Notifications."""
        if url_code == 'editorial_page':
            return reverse(
                'submissions:editorial_page', args=(self.submission.preprint.identifier_w_vn_nr,))
        return self.get_absolute_url()
