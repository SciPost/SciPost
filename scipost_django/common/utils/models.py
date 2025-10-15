import importlib
from itertools import groupby

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db.models import (
    F,
    Q,
    Count,
    Field,
    ForeignObjectRel,
    Model,
    QuerySet,
    Subquery,
    OuterRef,
)
from django.db.models.fields.related import RelatedField

from typing import Any, TypeVar

TQuery = TypeVar("TQuery", bound=Q | F)
M = TypeVar("M", bound=Model)


def get_current_domain():
    try:
        return Site.objects.get_current().domain
    except:
        return "fake.domain"


def merge(old, new):
    """
    Merge two model instances, `old` and `new`, by:
    - copying all the fields from `old` to `new` if they are not already set
    - updating all (reverse) relations from `old` to `new`
    """
    model = old.__class__

    for field in model._meta.get_fields():
        accessor = field.name or field.get_accessor_name()
        old_value = getattr(old, accessor, None)

        if isinstance(field, Field):
            # If new object has a value for the field, skip it
            # otherwise, set the value from the old object
            if getattr(new, accessor, None) is None:
                setattr(new, accessor, old_value)
        elif isinstance(field, RelatedField) or isinstance(field, ForeignObjectRel):
            # Handle object relations
            related_object = field
            manager = related_object.related_model.objects

            # Guard against missing related object field names
            if not hasattr(related_object, "field"):
                continue

            field_name = related_object.field.name

            if related_object.one_to_one:
                # For one-to-one relations, we get the related objects from the manager
                # and anull (let go) the attribute of the new object
                # so that it can be attached it to the old object
                # =====================
                # Equivalent to:
                # new.field_name = None
                # old.field_name = new
                manager.filter(**{field_name: new}).update(**{field_name: None})
                manager.filter(**{field_name: old}).update(**{field_name: new})
            elif related_object.many_to_many:
                # For many-to-many relations, `old_value` is a manager
                # and we can add the related objects to the new object
                if accessor is not None and old_value is not None:
                    getattr(new, accessor).add(*old_value.all())
                else:
                    for related_queryset in manager.filter(**{field_name: old}):
                        getattr(related_queryset, accessor).remove(old)
                        getattr(related_queryset, accessor).add(new)
            elif related_object.one_to_many:
                # For one-to-many relations, we get the related objects from the manager
                # and update the foreign key to the new object
                manager.filter(**{field_name: old}).update(**{field_name: new})
            else:
                # Handle many-to-one relations by setting the attribute
                # of the new object if it is not already set
                if getattr(new, accessor) is None:
                    setattr(new, accessor, old_value)

        else:
            # Handle fields by setting the attribute of the new object
            # if it is not already set
            if getattr(new, accessor) is None:
                setattr(new, accessor, old_value)

    # Save both objects
    new.save()
    old.save()


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
