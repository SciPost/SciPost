__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from dataclasses import dataclass

from django.db.models import Model, QuerySet

from typing import Any, Iterator, Iterable, TypeVar

M = TypeVar("M", bound=Model)
N = TypeVar("N", bound=Model)


@dataclass
class RelatedAttachment[M, N]:
    """
    Describes how to attach related objects to model instances.
    Used by `attach_related` to fetch and set related objects on models.

    Attributes:
        source_field (str): The field on the source model that holds the foreign key to the related model.
        target_field (str): The field on the source model where the related object will be attached.
        queryset (QuerySet[Model] | None): An optional queryset to fetch related objects from. If not provided,
            the related model will be inferred from the source field. Useful for optimizing queries through
            prefetching or filtering unwanted related objects.

    Types:
        M: The type of the related model instances to be attached.
        N: The type of the original model instances to which related objects will be attached.
    """

    source_field: str
    target_field: str
    queryset: QuerySet[M] | None = None

    def get_queryset(self, object_iterator: Iterator[M | None]) -> QuerySet[M]:
        """
        Retrieves the queryset from which to fetch related objects,
        either from the provided queryset or by inferring it from the model's source field.
        """
        if self.queryset is not None:
            return self.queryset
        elif object_iterator and (object := next(iter(object_iterator), None)):
            model_field = object._meta.get_field(self.source_field)
            if related_model := model_field.related_model:
                return related_model._default_manager.all()
            else:
                raise ValueError(
                    f"Cannot infer related model from field '{self.source_field}'."
                )
        else:
            raise ValueError(
                "Either 'queryset' must be provided or 'object' must not be None."
            )

    def fetch_related(self, objects: Iterable[M]) -> Iterable[M]:
        """
        Fetches related objects for the given model instances.

        Args:
            objects (Iterable[Model]): An iterable of Django model instances.

        Returns:
            Iterable[Model]: An iterable of *related* Django model instances.
        """
        if isinstance(objects, QuerySet):
            pks = objects.values_list(self.source_field, flat=True)
        else:
            pks = {getattr(obj, self.source_field) for obj in objects}

        qs = self.get_queryset(iter(objects))
        return qs.filter(pk__in=pks)

    def apply_to(self, objects: Iterable[N]) -> None:
        """Shortcut to fetch and attach related objects to the given model instances."""

        return attach_related(objects, self)


def attach_related(objects: Iterable[N], *attachments: RelatedAttachment[M, N]) -> None:
    """
    Attaches related objects to model instances like Django's `prefetch_related_objects`,
    but works for `select_related`-style relations as well.

    Args:
        objects (Iterable[Model]): An iterable of Django model instances.
        *attachments (RelatedAttachment): RelatedAttachments defining how to fetch and attach related objects.

    Returns:
        None, modifies the objects in place.
    """

    for attachment in attachments:
        attachment_map = {obj.pk: obj for obj in attachment.fetch_related(objects)}

        for obj in objects:
            related_obj = attachment_map.get(getattr(obj, attachment.source_field))
            setattr(obj, attachment.target_field, related_obj)


class AttachableQuerySet(QuerySet[M]):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._attachments: list[RelatedAttachment[Model, M]] = []
        self._attaching_done = False

    @classmethod
    def from_queryset(cls, queryset: QuerySet[M]) -> "AttachableQuerySet[M]":
        """
        Creates an AttachableQuerySet from a regular QuerySet, copying its data and annotations.

        Args:
            queryset (QuerySet[M]): The original QuerySet to copy.

        Returns:
            AttachableQuerySet[M]: A new AttachableQuerySet instance with the same data and
            annotations as the original QuerySet.
        """
        attachable_qs = cls()

        for attr in ["model", "query", "_result_cache", "_prefetch_related_lookups"]:
            value = getattr(queryset, attr)
            setattr(attachable_qs, attr, value)

        return attachable_qs

    def _clone(self) -> "AttachableQuerySet[M]":
        c = super()._clone()

        c._attachments = self._attachments.copy()
        c._attaching_done = self._attaching_done

        return c

    def attach(
        self, *attachments: RelatedAttachment[Model, M]
    ) -> "AttachableQuerySet[M]":
        """
        Adds attachments to the queryset, which will be applied when the queryset is evaluated.
        Attachments are used to fetch and set related objects on the models in the queryset.

        Args:
            *attachments (RelatedAttachment): One or more RelatedAttachment instances defining how to fetch and attach related objects.

        Returns:
            AttachableQuerySet[M]: The same queryset instance with the attachments added.
        """
        self._attachments.extend(attachments)
        return self

    def _fetch_all(self):
        super()._fetch_all()

        if self._attachments and not self._attaching_done:
            attach_related(self._result_cache, *self._attachments)
            self._attaching_done = True
