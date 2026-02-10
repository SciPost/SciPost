__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from ..managers import QualificationQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scipost.models import Contributor
    from submissions.models.submission import Submission


class Qualification(models.Model):
    """
    Specification of a Fellow's qualification for handling a Submission.
    """

    EXPERT = "expert"
    VERY_KNOWLEDGEABLE = "very_knowledgeable"
    KNOWLEDGEABLE = "knowledgeable"
    MARGINALLY_QUALIFIED = "marginally_qualified"
    NOT_REALLY_QUALIFIED = "not_really_qualified"
    NOT_AT_ALL_QUALIFIED = "not_at_all_qualified"
    EXPERTISE_LEVEL_CHOICES = (
        (EXPERT, "Expert"),
        (VERY_KNOWLEDGEABLE, "Very knowledgeable"),
        (KNOWLEDGEABLE, "Knowledgeable"),
        (MARGINALLY_QUALIFIED, "Marginally qualified"),
        (NOT_REALLY_QUALIFIED, "Not really qualified"),
        (NOT_AT_ALL_QUALIFIED, "Not at all qualified"),
    )
    EXPERTISE_QUALIFIED = [
        EXPERT,
        VERY_KNOWLEDGEABLE,
        KNOWLEDGEABLE,
        MARGINALLY_QUALIFIED,
    ]
    EXPERTISE_NOT_QUALIFIED = [
        NOT_REALLY_QUALIFIED,
        NOT_AT_ALL_QUALIFIED,
    ]

    submission = models.ForeignKey["Submission"](
        "submissions.Submission",
        on_delete=models.CASCADE,
    )

    fellow = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
    )

    expertise_level = models.CharField(
        max_length=32,
        choices=EXPERTISE_LEVEL_CHOICES,
        blank=True,
    )

    comments = models.TextField(blank=True)

    datetime = models.DateTimeField(default=timezone.now)

    objects = QualificationQuerySet.as_manager()

    class Meta:
        default_related_name = "qualifications"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "fellow"],
                name="qualification_unique_together_submission_fellow",
            ),
        ]
        ordering = ["submission", "fellow"]

    def __str__(self):
        return (
            f"{self.fellow}: {self.get_expertise_level_display()} "
            f"(for {self.submission})"
        )

    @property
    def is_qualified(self):
        return self.expertise_level in self.EXPERTISE_QUALIFIED
