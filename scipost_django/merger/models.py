__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from itertools import combinations
import json

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize

from typing import TYPE_CHECKING, Any, Iterable, Self, TypeVar

from merger.utils import get_field_name, resolve_field_value

M = TypeVar("M", bound=models.Model)

if TYPE_CHECKING:
    from scipost.models import Contributor


class NonDuplicateMark(models.Model):
    """
    Entity to mark two objects as non-duplicates of each other.
    Object A and Object B must be of the same model (enforced by content_type).
    The ordering of A and B is enforced (A < B) to avoid duplicate declarations.
    """

    marked_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="non_duplicates_marked",
    )
    description = models.TextField(blank=True)

    content_type = models.ForeignKey["ContentType"](
        "contenttypes.ContentType", on_delete=models.CASCADE
    )

    object_a_pk = models.PositiveIntegerField()
    object_b_pk = models.PositiveIntegerField()

    object_a = GenericForeignKey("content_type", "object_a_pk")
    object_b = GenericForeignKey("content_type", "object_b_pk")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: list[models.BaseConstraint] = [
            models.UniqueConstraint(
                fields=["content_type", "object_a_pk", "object_b_pk"],
                name="unique_non_duplicate_mark",
                violation_error_message="This non-duplicate declaration already exists",
            ),
            models.CheckConstraint(
                check=models.Q(object_a_pk__lt=models.F("object_b_pk")),
                name="a_lt_b_non_duplicate_mark",
                violation_error_message="To avoid duplicate declarations, object_a_pk must be less than object_b_pk",
            ),
        ]
        verbose_name = "Non-duplicate"
        verbose_name_plural = "Non-duplicates"

    @property
    def model_name_plural(self):
        if model_class := self.content_type.model_class():
            return str(model_class._meta.verbose_name_plural).title()
        return "[Unknown]"

    def __str__(self):
        return f"Marked non-duplicate {self.model_name_plural} ({self.object_a_pk}, {self.object_b_pk})"

    def resolve_inconsistencies(self, commit: bool = True):
        """
        Re-order objects to ensure object_a_pk < object_b_pk.
        """
        if self.object_a_pk > self.object_b_pk:
            self.object_a, self.object_b = self.object_b, self.object_a

        if commit:
            self.save()

        return self

    @classmethod
    def from_objects(
        cls,
        *objects: models.Model,
        marked_by: "Contributor | None" = None,
        description: str = "",
    ) -> Iterable[Self]:
        # Assure that the objects are not duplicates of each other
        # and sort them by their primary key to avoid duplicate declarations
        # `set` works because it hashes the .pk of the models
        objects = tuple(sorted(set(objects), key=lambda x: x.pk))
        if len(objects) < 2:
            raise ValueError("At least two objects must be provided")

        model = objects[0]._meta.model
        if not all(obj._meta.model == model for obj in objects[1:]):
            raise ValueError("All objects must be of the same model")

        content_type = ContentType.objects.get_for_model(model)
        for a, b in combinations(objects, 2):
            yield cls(
                marked_by=marked_by,
                description=description,
                content_type=content_type,
                object_a=a,
                object_b=b,
            )


class MergeHistoryRecord(models.Model):
    """
    Record of a merge operation between two objects.
    The deprecated object is the one that was removed, the kept object is the one that remains.
    Both objects must be of the same model (enforced by content_type).
    This model also stores who performed the merge, when, and any options used during the merge.
    """

    performed_by = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        null=True,
        related_name="merges_performed",
    )
    description = models.TextField(blank=True)

    content_type = models.ForeignKey["ContentType"](
        "contenttypes.ContentType", on_delete=models.CASCADE
    )

    deprecated_object_pk = models.PositiveIntegerField()
    kept_object_pk = models.PositiveIntegerField()

    deprecated = GenericForeignKey("content_type", "deprecated_object_pk")
    kept = GenericForeignKey("content_type", "kept_object_pk")

    created = models.DateTimeField(auto_now_add=True)

    options = models.JSONField[dict[str, Any]](
        blank=True,
        default=dict,
        help_text="Options used during the merge operation",
    )
    deprecated_snapshot = models.JSONField[dict[str, Any]](
        help_text="Snapshot of the deprecated object before deletion",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Merge history record"
        verbose_name_plural = "Merge history records"
        ordering = ["created"]

    @property
    def model_name_plural(self):
        if model_class := self.content_type.model_class():
            return str(model_class._meta.verbose_name_plural).title()
        return "[Unknown]"

    def __str__(self):
        return f"Record of merging {self.model_name_plural} {self.deprecated_object_pk}[-] -> {self.kept_object_pk}[+]"

    @classmethod
    def from_operation(
        cls,
        deprecated: M,
        kept: M,
        options: dict[str, Any] | None = None,
        performed_by: "Contributor | None" = None,
        description: str = "",
    ):
        try:
            snapshot: str = json.dumps(cls._serialize_object_and_relations(deprecated))
        except BaseException:
            snapshot = json.dumps(deprecated.__dict__)

        return cls(
            performed_by=performed_by,
            description=description,
            content_type=ContentType.objects.get_for_model(deprecated),
            deprecated=deprecated,
            kept=kept,
            options=options,
            deprecated_snapshot=snapshot,
        )

    @staticmethod
    def _serialize_object_and_relations(obj: models.Model) -> dict[str, Any]:
        """
        Serialize an object and its related objects to a dictionary.
        """
        data = {
            "str": str(obj),
            "object": serialize("json", [obj]),
            "related": {},
        }

        for field in obj._meta.get_fields():
            # Only consider auto-created reverse relations
            if isinstance(field, models.AutoField) or not field.auto_created:
                continue

            _, values = resolve_field_value(obj, field, use_display=False)
            serialization_options = {}
            if list(filter(lambda x: x is not None, values)):
                # Save all fields when deletion strategy is CASCADE
                # otherwise only save the primary key of the related object
                if (
                    field.on_delete
                    and field.on_delete.__code__ != models.CASCADE.__code__
                ):
                    serialization_options = dict(
                        fields=[get_field_name(field.remote_field)]
                    )

                data["related"][field.name] = serialize(
                    "json", values, **serialization_options
                )

        return data
