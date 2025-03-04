__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from scipost.models import Contributor


class NonDuplicate(models.Model):
    contributor = models.ForeignKey[Contributor](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="non_duplicates_marked",
    )
    description = models.TextField(blank=True)

    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.CASCADE
    )

    object_a_id = models.PositiveIntegerField()
    object_b_id = models.PositiveIntegerField()

    object_a = GenericForeignKey("content_type", "object_a_id")
    object_b = GenericForeignKey("content_type", "object_b_id")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_a_id", "object_b_id"],
                name="unique_non_duplicate",
                violation_error_message="This non-duplicate declaration already exists",
            ),
            models.CheckConstraint(
                check=models.Q(object_a_id__lt=models.F("object_b_id")),
                name="object_a_lt_object_b",
                violation_error_message="To avoid duplicate declarations, object_a_id must be less than object_b_id",
            ),
        ]
        verbose_name = "Non-duplicate"
        verbose_name_plural = "Non-duplicates"

    def __str__(self):
        return f"NonDuplicate {str(self.content_type.model_class()._meta.verbose_name_plural).title()} ({self.object_a_id}, {self.object_b_id})"
