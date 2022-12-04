__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse

from ..constants import PLAGIARISM_STATUSES, STATUS_WAITING, STATUS_RECEIVED

from scipost.behaviors import TimeStampedModel


class iThenticateReport(TimeStampedModel):
    """iThenticate plagiarism report for a Submission."""

    uploaded_time = models.DateTimeField(null=True, blank=True)
    processed_time = models.DateTimeField(null=True, blank=True)
    doc_id = models.IntegerField(primary_key=True)
    part_id = models.IntegerField(null=True, blank=True)
    percent_match = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=PLAGIARISM_STATUSES, default=STATUS_WAITING
    )

    class Meta:
        verbose_name = "iThenticate Report"
        verbose_name_plural = "iThenticate Reports"

    def __str__(self):
        """Summary of the iThenticateReport's meta information."""
        _str = "Report {doc_id}".format(doc_id=self.doc_id)
        if hasattr(self, "to_submission"):
            _str += " on Submission {arxiv}".format(
                arxiv=self.to_submission.preprint.identifier_w_vn_nr
            )
        return _str

    def save(self, *args, **kwargs):
        """On save, touch the Submission's latest update timestamp."""
        obj = super().save(*args, **kwargs)
        if hasattr(self, "to_submission") and kwargs.get("commit", True):
            self.to_submission.touch()
        return obj

    def get_absolute_url(self):
        """Return the url of the Submission's plagiarism report detail page."""
        if hasattr(self, "to_submission"):
            return reverse(
                "submissions:plagiarism",
                kwargs={
                    "identifier_w_vn_nr": self.to_submission.preprint.identifier_w_vn_nr
                },
            )
        return ""

    def get_report_url(self):
        """Request and return new read-only url from the iThenticate API.

        Note: The read-only link is valid for only 15 minutes, saving may be worthless.
        """
        if not self.part_id:
            return ""

        from ..plagiarism import iThenticate

        plagiarism = iThenticate()
        return plagiarism.get_url(self.part_id)

    @property
    def processed(self):
        return self.processed_time is not None

    @property
    def score(self):
        """Return the iThenticate score returned by their API as saved in the database."""
        return self.percent_match
