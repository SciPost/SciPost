__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from ..managers import QualificationQuerySet


class Qualification(models.Model):
    """
    Specification of a Fellow's qualification for handlind a Submission.
    """

    EXPERT = "expert"
    VERY_KNOWLEDGEABLE = "very_knowledgeable"
    KNOWLEDGEABLE = "knowledgeable"
    MARGINALLY_QUALIFIED = "marginally_qualified"
    NOT_REALLY_QUALIFIED = "not_really_qualified"
    NOT_AT_ALL_QUALIFIED = "not_at_all_qualified"
    EXPERTISE_LEVEL_CHOICES = (
        (EXPERT, "Expert in this subject"),
        (VERY_KNOWLEDGEABLE, "Very knowledgeable in this subject"),
        (KNOWLEDGEABLE, "Knowledgeable in this subject"),
        (MARGINALLY_QUALIFIED, "Marginally qualified"),
        (NOT_REALLY_QUALIFIED, "Not really qualified"),
        (NOT_AT_ALL_QUALIFIED, "Not at all qualified"),
    )

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
    )

    fellow = models.ForeignKey(
        "colleges.Fellowship",
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
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "fellow"],
                name="unique_together_submission_fellow",
            ),
        ]
        ordering =["submission", "fellow"]


    def __str__(self):
        return (f"{self.fellow}: {self.get_expertise_level_display()} "
                f"(for {self.submission})")

    @property
    def is_qualified(self):
        return self.expertise_level in [
            self.EXPERT,
            self.VERY_KNOWLEDGEABLE,
            self.KNOWLEDGEABLE,
            self.MARGINALLY_QUALIFIED,
        ]
