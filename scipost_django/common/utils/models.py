import importlib
from itertools import groupby
from dataclasses import dataclass

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db.models import F, Q, Count, Model, QuerySet, Subquery, OuterRef

from typing import Any, TypeVar, Iterable


TQuery = TypeVar("TQuery", bound=Q | F)
M = TypeVar("M", bound=Model)


def get_current_domain():
    try:
        return Site.objects.get_current().domain
    except:
        return "fake.domain"


def model_eval_attr(obj: Model | QuerySet[Model], attr_path: str) -> Any:
    """
    Evaluates an attribute path against a Model/QuerySet recursively.
    e.g. converts `"organization.id"` to `object.organization.id`
    """
    if "." in attr_path:
        attr, rest = attr_path.split(".", 1)
    else:
        attr, rest = attr_path, None

    if isinstance(obj, dict) and attr in obj:
        obj_attr = obj[attr]
    else:
        obj_attr = getattr(obj, attr)

    if rest:
        return model_eval_attr(obj_attr, attr_path=rest)
    else:
        return obj_attr


def parametrize_query(query: TQuery, obj: Model) -> TQuery:
    # Deconstruct query to access values and parametrize them
    model_str, args, kwargs = query.deconstruct()

    # Import the symbol deconstructed so that it may be reinstanciated
    namespace_str, symbol_str = model_str.rsplit(".", 1)
    module = importlib.import_module(namespace_str)
    symbol = getattr(module, symbol_str)

    parameterized_args = []
    for arg in args:
        if not isinstance(arg, tuple):
            # In case this is another composable Q/F, recurse
            parameterized_arg = parametrize_query(arg, obj)
        else:
            # This is a regular value, evaluate the str value against the object
            key, value = arg
            evaluated_attribute = model_eval_attr(obj, value)

            if eval_attr_all := getattr(evaluated_attribute, "all", None):
                # If this is a Queryset or Manager, run .all() on it to obtain usable models
                # Also append default "__in" to the filter key
                parameterized_arg = (key + "__in", eval_attr_all())
            else:
                # Otherwise simply use the evaluated attribute with the same key
                parameterized_arg = (key, evaluated_attribute)

        parameterized_args.append(parameterized_arg)

    # Reconstruct the query obj exactly as it was, but with the evaluated attributes
    return symbol(*parameterized_args, **kwargs)


def qs_duplicates_group_by_key(qs: QuerySet[M], key: str) -> "groupby[str, M]":
    """
    Groups a queryset by a given key and returns an iterator of groups with more than one item.
    Useful for finding potential duplicates based on a specific field.
    """
    from merger.models import NonDuplicateMark

    def not_fully_marked(among: list[M]):
        def item_not_fully_marked(item: M) -> bool:
            non_duplicate_marks = getattr(item, "nr_non_duplicate_marks", 0) or 0
            return non_duplicate_marks < len(among) - 1

        return item_not_fully_marked

    groups = list(
        qs.values(key)
        .annotate(nr_count=Count(key))
        .filter(nr_count__gt=1)
        .values_list(key, flat=True)
    )
    duplicates = (
        qs.annotate(
            nr_non_duplicate_marks=Subquery(
                NonDuplicateMark.objects.filter(
                    Q(object_a_pk=OuterRef("pk")) | Q(object_b_pk=OuterRef("pk")),
                    content_type=ContentType.objects.get_for_model(qs.model),
                )
                .values("content_type")
                .annotate(count=Count("content_type"))
                .values("count")[:1]
            )
        )
        .filter(**{key + "__in": groups})
        .order_by(key, "-id")
    )
    groups = groupby(
        duplicates, key=lambda c: model_eval_attr(c, key.replace("__", "."))
    )

    groups_not_fully_marked = (
        # Return the same iterator structure as groupby, but filtering
        # out items that are fully marked as non-duplicates within their group
        (group, filtered)
        # Groupby iterator has to be exhausted to get its length for the filter
        for group, item_list in [(group, list(items)) for group, items in groups]
        if (filtered := list(filter(not_fully_marked(among=item_list), item_list)))
    )

    return groups_not_fully_marked


@dataclass
class RelatedAttachment:
    """
    Describes how to attach related objects to model instances.
    Used by `attach_related` to fetch and set related objects on models.

    Attributes:
        source_field (str): The field on the source model that holds the foreign key to the related model.
        target_field (str): The field on the source model where the related object will be attached.
        queryset (QuerySet[Model] | None): An optional queryset to fetch related objects from. If not provided,
            the related model will be inferred from the source field. Useful for optimizing queries through
            prefetching or filtering unwanted related objects.
    """

    source_field: str
    target_field: str
    queryset: QuerySet[Model] | None = None

    def get_queryset(self, object: Model | None = None) -> QuerySet[Model]:
        """
        Retrieves the queryset to fetch related objects, either from the provided queryset
        or by inferring it from the model's source field.
        """
        if self.queryset is not None:
            return self.queryset
        elif object is not None:
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

    def fetch_related(self, objects: Iterable[Model]) -> Iterable[Model]:
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

        qs = self.get_queryset(next(iter(objects), None))
        return qs.filter(pk__in=pks)

    def apply_to(self, objects: Iterable[Model]) -> None:
        """Shortcut to fetch and attach related objects to the given model instances."""

        return attach_related(objects, self)


def attach_related(objects: Iterable[Model], *attachments: RelatedAttachment) -> None:
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
