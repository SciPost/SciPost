__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..constants import EDITORIAL_DECISION_CHOICES, EIC_REC_PUBLISH
from ..managers import EditorialDecisionQuerySet


class EditorialDecision(models.Model):
    """Editorial decision, created by EdAdmin based on voting results.

    If the decision is to publish in the journal the authors submitted to,
    or in a higher one (e.g. Selections instead of flagship), authors are
    presumed to accept the outcome.

    If the decision is to publish in a Journal which is subsidiary to the one
    the authors submitted to, the authors are sent a publication offer which
    they have to accept before production is initiated.
    """

    DRAFTED = 0
    FIXED_AND_ACCEPTED = 1
    AWAITING_PUBOFFER_ACCEPTANCE = 2
    PUBOFFER_REFUSED_BY_AUTHORS = 3
    APPEALED_BY_AUTHORS = 4
    UNDER_REVIEW_BY_OMBUDSPERSON = 5
    DEPRECATED = -1
    EDITORIAL_DECISION_STATUSES = (
        (DRAFTED, "Editorial decision drafted (yet to be communicated to authors)"),
        (
            FIXED_AND_ACCEPTED,
            "Editorial decision fixed and (if required) accepted by authors",
        ),
        (
            AWAITING_PUBOFFER_ACCEPTANCE,
            "Awaiting author acceptance of publication offer",
        ),
        (
            PUBOFFER_REFUSED_BY_AUTHORS,
            "Publication offer refused by authors; manuscript will not be produced",
        ),
        (APPEALED_BY_AUTHORS, "Editorial decision appealed by authors"),
        (
            UNDER_REVIEW_BY_OMBUDSPERSON,
            "Editorial decision under review by ombudsperson",
        ),
        (DEPRECATED, "Deprecated"),
    )

    submission = models.ForeignKey("submissions.Submission", on_delete=models.CASCADE)
    for_journal = models.ForeignKey("journals.Journal", on_delete=models.CASCADE)
    decision = models.SmallIntegerField(choices=EDITORIAL_DECISION_CHOICES)
    taken_on = models.DateTimeField(default=timezone.now)
    remarks_for_authors = models.TextField(
        blank=True, verbose_name="optional remarks for the authors"
    )
    remarks_for_editorial_college = models.TextField(
        blank=True, verbose_name="optional remarks for the Editorial College"
    )
    status = models.SmallIntegerField(choices=EDITORIAL_DECISION_STATUSES)
    version = models.SmallIntegerField(default=1)

    objects = EditorialDecisionQuerySet.as_manager()

    class Meta:
        ordering = ["-submission__submission_date", "-version"]
        unique_together = ["submission", "version"]
        verbose_name = "Editorial Decision"
        verbose_name_plural = "Editorial Decisions"

    def __str__(self):
        return "%s: %s for journal %s" % (
            self.submission.preprint.identifier_w_vn_nr,
            self.get_decision_display(),
            self.for_journal,
        )

    def summary(self):
        return "For Journal %s: %s (status: %s)" % (
            self.for_journal,
            self.get_decision_display(),
            self.get_status_display(),
        )

    def get_absolute_url(self):
        return reverse(
            "submissions:editorial_decision_detail",
            kwargs={"identifier_w_vn_nr": self.submission.preprint.identifier_w_vn_nr},
        )

    @property
    def is_fixed_and_accepted(self):
        return self.status == self.FIXED_AND_ACCEPTED

    @property
    def publish(self):
        """Whether the decision is to publish (True) or reject (False)."""
        return self.decision == EIC_REC_PUBLISH

    @property
    def production_can_proceed(self):
        return self.status == self.FIXED_AND_ACCEPTED
