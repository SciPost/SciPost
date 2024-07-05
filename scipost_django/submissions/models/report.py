__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import subprocess
from typing import TYPE_CHECKING
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property

from scipost.storage import SecureFileStorage
from comments.behaviors import validate_file_extension, validate_max_file_size
from journals.models import Publication
from submissions.utils import clean_pdf, linearize_pdf, remove_file_metadata

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import (
    REPORT_TYPES,
    REPORT_NORMAL,
    REPORT_STATUSES,
    STATUS_DRAFT,
    STATUS_UNVETTED,
    STATUS_VETTED,
    STATUS_INCORRECT,
    STATUS_UNCLEAR,
    STATUS_NOT_USEFUL,
    STATUS_NOT_ACADEMIC,
    REFEREE_QUALIFICATION,
    RANKING_CHOICES,
    QUALITY_SPEC,
    REPORT_REC,
)
from ..managers import ReportQuerySet

if TYPE_CHECKING:
    from scipost.models import Contributor
    from submissions.models import Submission


class Report(SubmissionRelatedObjectMixin, models.Model):
    """Report on a Submission, written by a Contributor."""

    status = models.CharField(
        max_length=16, choices=REPORT_STATUSES, default=STATUS_UNVETTED
    )
    report_type = models.CharField(
        max_length=32, choices=REPORT_TYPES, default=REPORT_NORMAL
    )
    submission = models.ForeignKey["Submission"](
        "submissions.Submission", related_name="reports", on_delete=models.CASCADE
    )
    report_nr = models.PositiveSmallIntegerField(
        default=0,
        help_text="This number is a unique number "
        "refeering to the Report nr. of "
        "the Submission",
    )
    vetted_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        related_name="report_vetted_by",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    # `invited' filled from RefereeInvitation objects at moment of report submission
    invited = models.BooleanField(default=False)

    # `flagged' if author of report has been flagged by submission authors (surname check only)
    flagged = models.BooleanField(default=False)
    author = models.ForeignKey["Contributor"](
        "scipost.Contributor", on_delete=models.CASCADE, related_name="reports"
    )
    qualification = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=REFEREE_QUALIFICATION,
        verbose_name="Qualification to referee this: I am",
    )

    # Text-based reporting
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    report = models.TextField(blank=True)
    requested_changes = models.TextField(verbose_name="requested changes", blank=True)

    # Comments can be added to a Submission
    comments = GenericRelation("comments.Comment", related_query_name="reports")

    # Qualities:
    validity = models.PositiveSmallIntegerField(
        choices=RANKING_CHOICES, null=True, blank=True
    )
    significance = models.PositiveSmallIntegerField(
        choices=RANKING_CHOICES, null=True, blank=True
    )
    originality = models.PositiveSmallIntegerField(
        choices=RANKING_CHOICES, null=True, blank=True
    )
    clarity = models.PositiveSmallIntegerField(
        choices=RANKING_CHOICES, null=True, blank=True
    )
    formatting = models.SmallIntegerField(
        choices=QUALITY_SPEC,
        null=True,
        blank=True,
        verbose_name="Quality of paper formatting",
    )
    grammar = models.SmallIntegerField(
        choices=QUALITY_SPEC,
        null=True,
        blank=True,
        verbose_name="Quality of English grammar",
    )

    recommendation = models.SmallIntegerField(null=True, blank=True, choices=REPORT_REC)
    recommendation_publicly_visible = models.BooleanField(default=True)
    remarks_for_editors = models.TextField(
        blank=True, verbose_name="optional remarks for the Editors only"
    )
    needs_doi = models.BooleanField(null=True, default=None)
    doideposit_needs_updating = models.BooleanField(default=False)
    genericdoideposit = GenericRelation(
        "journals.GenericDOIDeposit", related_query_name="genericdoideposit"
    )
    doi_label = models.CharField(max_length=200, blank=True)
    anonymous = models.BooleanField(default=True, verbose_name="Publish anonymously")
    pdf_report = models.FileField(
        upload_to="UPLOADS/REPORTS/%Y/%m/", max_length=200, blank=True
    )

    date_submitted = models.DateTimeField("date submitted")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # Attachment
    file_attachment = models.FileField(
        upload_to="uploads/reports/%Y/%m/%d/",
        blank=True,
        validators=[validate_file_extension, validate_max_file_size],
        storage=SecureFileStorage(),
    )

    objects = ReportQuerySet.as_manager()

    class Meta:
        unique_together = ("submission", "report_nr")
        default_related_name = "reports"
        ordering = ["-date_submitted"]

    def __str__(self):
        """Summarize the RefereeInvitation's basic information."""
        text = "Anonymous"
        if not self.anonymous:
            text = self.author.user.first_name + " " + self.author.user.last_name
        return (
            text
            + " on "
            + self.submission.title[:50]
            + " by "
            + self.submission.author_list[:50]
        )

    def save(self, *args, **kwargs):
        """Update report number before saving on creation."""
        if not self.report_nr:
            new_report_nr = self.submission.reports.aggregate(
                models.Max("report_nr")
            ).get("report_nr__max")
            if new_report_nr:
                new_report_nr += 1
            else:
                new_report_nr = 1
            self.report_nr = new_report_nr

        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return url of the Report on the Submission detail page."""
        return self.submission.get_absolute_url() + "#report_" + str(self.report_nr)

    def get_attachment_url(self):
        """Return url of the Report its attachment if exists."""
        return reverse(
            "submissions:report_attachment",
            kwargs={
                "identifier_w_vn_nr": self.submission.preprint.identifier_w_vn_nr,
                "report_nr": self.report_nr,
            },
        )

    @property
    def is_in_draft(self):
        """Return if Report is in draft."""
        return self.status == STATUS_DRAFT

    @property
    def is_vetted(self):
        """Return if Report is publicly available."""
        return self.status == STATUS_VETTED

    @property
    def is_unvetted(self):
        """Return if Report is awaiting vetting."""
        return self.status == STATUS_UNVETTED

    @property
    def is_rejected(self):
        """Return if Report is rejected."""
        return self.status in [
            STATUS_INCORRECT,
            STATUS_UNCLEAR,
            STATUS_NOT_USEFUL,
            STATUS_NOT_ACADEMIC,
        ]

    @property
    def doi_string(self):
        """Return the doi with the registrant identifier prefix."""
        if self.doi_label:
            return "10.21468/" + self.doi_label
        return ""

    @cached_property
    def title(self):
        """Return the submission's title.

        This property is (mainly) used to let Comments get the title of the Submission without
        overcomplicated logic.
        """
        return self.submission.title

    @property
    def is_followup_report(self):
        """Return if Report is a follow-up Report instead of a regular Report.

        This property is used in the ReportForm, but will be candidate to become a database
        field if this information becomes necessary in more general information representation.
        """
        return (
            self.author.reports.accepted()
            .filter(
                submission__thread_hash=self.submission.thread_hash,
                submission__submission_date__lt=self.submission.submission_date,
            )
            .exists()
        )

    @property
    def associated_publication(self) -> Publication | None:
        """Return the related Publication object.

        Check if the Report relates to a SciPost-published object. If it does, return the
        Publication object.
        """
        return (
            Publication.objects.filter(
                accepted_submission__thread_hash=self.submission.thread_hash
            )
            .order_by("doi_label")
            .first()
        )  # order by doi_label to give priority to main article, which has no DOI suffix

    @property
    def relation_to_published(self):
        """Return dictionary with published object information.

        Check if the Report relates to a SciPost-published object. If it does, return a dict with
        info on relation to the published object, based on Crossref's peer review content type.
        """
        publication = (
            Publication.objects.filter(
                accepted_submission__thread_hash=self.submission.thread_hash
            )
            .order_by("doi_label")
            .first()
        )

        if publication:
            relation = {
                "isReviewOfDOI": publication.doi_string,
                "stage": "pre-publication",
                "type": "referee-report",
                "title": "Report on " + self.submission.preprint.identifier_w_vn_nr,
                "contributor_role": "reviewer",
            }
            return relation

    @property
    def citation(self):
        """Return the proper citation format for this Report."""
        citation = ""
        if self.doi_string:
            if self.anonymous:
                citation += "Anonymous, "
            else:
                citation += "%s %s, " % (
                    self.author.user.first_name,
                    self.author.user.last_name,
                )
            citation += (
                "Report on arXiv:%s, " % self.submission.preprint.identifier_w_vn_nr
            )
            citation += "delivered %s, " % self.date_submitted.strftime("%Y-%m-%d")
            citation += "doi: %s" % self.doi_string
        return citation

    def create_doi_label(self):
        """Create a doi in the default format."""
        Report.objects.filter(id=self.id).update(
            doi_label="SciPost.Report.{}".format(self.id)
        )

    def latest_report_from_thread(self):
        """Get latest Report of this Report's author for the Submission thread."""
        return (
            self.author.reports.accepted()
            .filter(submission__thread_hash=self.submission.thread_hash)
            .order_by("submission__submission_date")
            .last()
        )


@receiver(post_save, sender=Report)
def clean_anonymous_report_pdf(sender, instance, created, **kwargs):
    if instance.pdf_report and instance.anonymous:
        clean_pdf(instance.pdf_report.path)
