__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

from submissions.managers import ReadinessQuerySet


class Readiness(models.Model):
    """
    Specification of a Fellow's readiness to take charge of a Submission.
    """

    STATUS_PERHAPS_LATER = "perhaps_later"
    STATUS_COULD_IF_TRANSFERRED = "could_if_transferred"
    STATUS_TOO_BUSY = "too_busy"
    STATUS_ON_VACATION = "on_vacation"
    STATUS_NOT_INTERESTED = "not_interested"
    STATUS_DESK_REJECT = "desk_reject"
    STATUS_CHOICES = (
        (STATUS_PERHAPS_LATER, "Perhaps later (if nobody else does)"),
        (
            STATUS_COULD_IF_TRANSFERRED,
            "I could (but only if transferred to lower journal)",
        ),
        (STATUS_TOO_BUSY, "Interesting, but I'm currently too busy"),
        (STATUS_ON_VACATION, "Interesting, but I'm currently on vacation"),
        (STATUS_NOT_INTERESTED, "I won't: I'm not interested enough"),
        (STATUS_DESK_REJECT, "I won't, and vote for desk rejection"),
    )

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
    )

    fellow = models.ForeignKey(
        "colleges.Fellowship",
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
    )

    comments = models.TextField(blank=True)

    datetime = models.DateTimeField(default=timezone.now)

    objects = ReadinessQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "fellow"],
                name="readiness_unique_together_submission_fellow",
            ),
        ]
        ordering =["submission", "fellow"]


    def __str__(self):
        return f"{self.fellow}: {self.get_status_display()} (for {self.submission})"
