__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db import models

from scipost.storage import SecureFileStorage

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from submissions.models import EditorialDecision
    from scipost.models import Contributor


class Appeal(models.Model):
    """An appeal of an editorial decision, created by authors and reviewed by Senior Fellow adjudicators."""

    DRAFTED = "drafted"
    STARTED = "started"
    COMPLETED = "completed"
    DEPRECATED = "deprecated"
    APPEAL_STATUSES = (
        (DRAFTED, "Drafted"),
        (STARTED, "Started"),
        (COMPLETED, "Completed"),
        (DEPRECATED, "Deprecated"),
    )

    editorial_decision = models.OneToOneField["EditorialDecision"](
        "submissions.EditorialDecision",
        related_name="appeal",
        on_delete=models.CASCADE,
    )
    status = models.CharField(max_length=32, choices=APPEAL_STATUSES)
    appeal_letter_text = models.TextField(
        verbose_name="Appeal letter text",
        help_text="Text of the appeal letter submitted by the authors",
    )
    appeal_letter_attachment = models.FileField(
        verbose_name="Appeal letter attachment",
        upload_to="uploads/appeals/%Y/%m/%d/",
        storage=SecureFileStorage(),
        blank=True,
        null=True,
    )
    remarks_edadmin = models.TextField(
        verbose_name="Remarks from Editorial Administration",
        help_text="Remarks by editorial administration to adjudicating fellows",
        blank=True,
        null=True,
    )
    adjudicators = models.ManyToManyField["Contributor", "Appeal"](
        "scipost.Contributor",
        related_name="appeals_adjudicated",
        blank=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        default_related_name = "appeals"
        ordering = ["-editorial_decision__submission"]
        constraints = [
            models.UniqueConstraint(
                name="unique_editorial_decision",
                fields=["editorial_decision"],
            )
        ]

    def __str__(self):
        return "[%s] Appeal of %s" % (
            self.get_status_display(),
            self.editorial_decision,
        )

    def get_absolute_url(self):
        return self.editorial_decision.get_absolute_url()

    def add_adjudicator(self, adjudicator: "Contributor"):
        """Add an adjudicator to the appeal."""

        # Check that adjudicator is an active senior fellow in
        # the submission's academic field (college)
        if not (
            adjudicator.fellowships.all()
            .senior()
            .active()
            .college_specialties_overlap_with_submission(
                self.editorial_decision.submission
            )
            .exists()
        ):
            raise ValueError(
                "Adjudicator must be an active senior fellow in the college defined by the submission's academic field."
            )

        self.adjudicators.add(adjudicator)

    def remove_adjudicator(self, adjudicator: "Contributor"):
        """Remove an adjudicator from the appeal."""
        self.adjudicators.remove(adjudicator)
