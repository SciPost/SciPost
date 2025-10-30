import enum

from django.contrib.contenttypes.fields import GenericRel
from django.db import transaction
from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    Model,
    Field,
    ForeignObjectRel,
)

from typing import Any, TypeVar


FieldValues = list[Model | None]
FieldOrRel = Field[Any, Any] | ForeignObjectRel
T = TypeVar("T")
M = TypeVar("M", bound=Model)


def get_field_name(field: Field[Any, Any] | ForeignObjectRel) -> str:
    field_name = field.name
    att_name = getattr(field, "attname", None)
    accessor_name = getattr(field, "accessor_name", None)

    final_field_name = accessor_name or att_name or field_name

    if field_name + "_id" == att_name:
        final_field_name = field_name

    return final_field_name


def resolve_field_value(
    object: Model,
    field: Field[Any, Any] | ForeignObjectRel,
    use_display: bool = True,
) -> tuple[str, FieldValues]:
    """
    Resolve a field of an object to a displayable format.
    Returns a dictionary of the field and its display name - value pair,
    where `value` is a model instance, a list of model instances, or None.
    """
    display_name = getattr(field, "verbose_name", field.name)
    field_name = get_field_name(field)

    def get_field_value(obj: Model, field_name: str):
        display_func = getattr(obj, f"get_{field_name}_display", None)
        if use_display and display_func is not None:
            return display_func()

        try:
            return getattr(obj, field_name)
        except Exception:
            return None

    if field.many_to_many or field.one_to_many:
        field_nameval = (
            display_name,
            list(getattr(object, field_name).all()),
        )
    else:
        field_nameval = (display_name, [get_field_value(object, field_name)])

    return field_nameval


class MergeChangeType(enum.Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    ORPHANED = "orphaned"
    DELETED = "deleted"

    @property
    def icon(self) -> str:
        match self:
            case self.UNCHANGED:
                return "circle-fill"
            case self.ADDED:
                return "plus-circle-fill"
            case self.REMOVED:
                return "dash-circle-fill"
            case self.ORPHANED:
                return "slash-circle-fill"
            case self.DELETED:
                return "exclamation-circle-fill"

    @property
    def icon_path(self) -> str:
        return f"bi/{self.icon}.html"

    @property
    def color(self) -> str:
        match self:
            case self.UNCHANGED:
                return "dark"
            case self.ADDED:
                return "success"
            case self.REMOVED:
                return "danger"
            case self.ORPHANED:
                return "warning"
            case self.DELETED:
                return "danger"


class MergeStrategy(enum.Enum):
    class FieldRetainment(enum.Enum):
        KEEP = "keep"
        REPLACE = "replace"
        COMBINE = "combine"

        def description(self) -> str:
            match self:
                case self.KEEP:
                    return "Keep the current value"
                case self.REPLACE:
                    return "Replace the current value with that from the merged object"
                case self.COMBINE:
                    return "Combine the values of both objects"

    class RelationDeprecation(enum.Enum):
        ORPHAN = "orphan"  # Move relations, leaving object orphan (requires null=True)
        DELETE = "delete"  # Move relations, allowing deletion of originals

        def description(self) -> str:
            match self:
                case self.ORPHAN:
                    return "Set outstanding relations to null, creating orphan objects"
                case self.DELETE:
                    return "Delete the outstanding relations entirely"

        @property
        def merge_change_type(self) -> "MergeChangeType":
            match self:
                case self.ORPHAN:
                    return MergeChangeType.ORPHANED
                case self.DELETE:
                    return MergeChangeType.DELETED

    KEEP = "keep"
    REPLACE = "replace"
    COMBINE = "combine"
    KEEP_ORPHAN = "keep_orphan"
    KEEP_DELETE = "keep_delete"
    REPLACE_ORPHAN = "replace_orphan"
    REPLACE_DELETE = "replace_delete"

    def description(self) -> str:
        retainment, deprecation = self.to_tuple()
        desc = retainment.description()
        if deprecation:
            desc += f"; {deprecation.description()}"
        return desc

    def to_tuple(self) -> tuple[FieldRetainment, RelationDeprecation | None]:
        match self:
            case self.KEEP:
                return (self.FieldRetainment.KEEP, None)
            case self.REPLACE:
                return (self.FieldRetainment.REPLACE, None)
            case self.COMBINE:
                return (self.FieldRetainment.COMBINE, None)
            case self.KEEP_ORPHAN:
                return (
                    self.FieldRetainment.KEEP,
                    self.RelationDeprecation.ORPHAN,
                )
            case self.KEEP_DELETE:
                return (
                    self.FieldRetainment.KEEP,
                    self.RelationDeprecation.DELETE,
                )
            case self.REPLACE_ORPHAN:
                return (
                    self.FieldRetainment.REPLACE,
                    self.RelationDeprecation.ORPHAN,
                )
            case self.REPLACE_DELETE:
                return (
                    self.FieldRetainment.REPLACE,
                    self.RelationDeprecation.DELETE,
                )
            case _:
                raise ValueError(f"Unknown strategy: {self}")

    @classmethod
    def from_tuple(
        cls, tup: tuple[FieldRetainment, RelationDeprecation | None]
    ) -> "MergeStrategy":
        match tup:
            case (cls.FieldRetainment.KEEP, None):
                return cls.KEEP
            case (cls.FieldRetainment.REPLACE, None):
                return cls.REPLACE
            case (cls.FieldRetainment.COMBINE, None):
                return cls.COMBINE
            case (cls.FieldRetainment.KEEP, cls.RelationDeprecation.ORPHAN):
                return cls.KEEP_ORPHAN
            case (cls.FieldRetainment.KEEP, cls.RelationDeprecation.DELETE):
                return cls.KEEP_DELETE
            case (cls.FieldRetainment.REPLACE, cls.RelationDeprecation.ORPHAN):
                return cls.REPLACE_ORPHAN
            case (cls.FieldRetainment.REPLACE, cls.RelationDeprecation.DELETE):
                return cls.REPLACE_DELETE
            case _:
                raise ValueError(f"Unknown strategy tuple: {tup}")

    @classmethod
    def default_for_field(
        cls,
        field: FieldOrRel,
        from_vals: FieldValues | None = None,
        to_vals: FieldValues | None = None,
    ) -> "MergeStrategy":
        """
        Returns the default strategy for a given field, based on its type.
        If values are provided, the strategy will be adjusted accordingly,
        e.g. if KEEP is default but the value is None, REPLACE will be chosen instead.
        """
        admissible_strategies = cls.get_admissible_strategies(field)
        default_strategy_candidates: list[MergeStrategy] = []

        def _first_admissible(*strategies: "MergeStrategy") -> "MergeStrategy":
            for strategy in strategies:
                if strategy in admissible_strategies:
                    return strategy
            raise ValueError(
                "No admissible strategy found", strategies, admissible_strategies
            )

        if field.many_to_many or field.one_to_many:
            default_strategy_candidates.append(cls.COMBINE)
        elif field.one_to_one or field.many_to_one:
            default_strategy_candidates.extend(
                (
                    cls.KEEP_ORPHAN,
                    cls.KEEP_DELETE,
                    cls.REPLACE_ORPHAN,
                    cls.REPLACE_DELETE,
                )
            )
        else:  # Fields
            default_strategy_candidates.extend((cls.KEEP, cls.REPLACE))
            if from_vals and all(v is None for v in from_vals):
                default_strategy_candidates.remove(cls.KEEP)
            if to_vals and all(v is None for v in to_vals):
                default_strategy_candidates.remove(cls.REPLACE)
            # ... but if both are None, we have to keep something
            if not default_strategy_candidates:
                default_strategy_candidates.append(cls.KEEP)

        return _first_admissible(*default_strategy_candidates)

    def _get_field_value(self, field: FieldOrRel, obj: Model) -> FieldValues:
        from django.db.models.manager import ManyToManyRelatedManager

        value = getattr(obj, field.name, None)
        if isinstance(value, ManyToManyRelatedManager):
            return list(value.all())
        return [value]

    def get_display_name(self) -> str:
        retainment, deprecation = self.to_tuple()
        display_str = retainment.value.capitalize()
        if deprecation:
            display_str += f" ({deprecation.value} relation)"

        return display_str

    @classmethod
    def get_admissible_strategies(cls, field: FieldOrRel) -> list["MergeStrategy"]:
        strategies: list["MergeStrategy"] = []

        if not field.is_relation:
            strategies.extend((cls.KEEP, cls.REPLACE))

        if field.many_to_many or field.one_to_many:
            strategies.append(cls.COMBINE)

        if field.is_relation:
            nullable = not field.auto_created and field.null
            remote_nullable = field.auto_created and field.remote_field.null
            if nullable or remote_nullable:
                strategies.extend((cls.KEEP_ORPHAN, cls.REPLACE_ORPHAN))
            strategies.extend((cls.KEEP_DELETE, cls.REPLACE_DELETE))

        return strategies


@transaction.atomic
def merge_objects(
    object_from: M,
    object_to: M,
    field_strategies: dict[FieldOrRel, MergeStrategy],
    dry_run: bool = False,
) -> None:
    def _set_resolve_save(
        obj: M,
        field: FieldOrRel,
        value: Any,
    ) -> M:
        field_name = get_field_name(field)

        # Special handling for GenericRel, which needs to
        # set the object_id field instead of the object itself
        if isinstance(field, GenericRel):
            value = value.pk if value else None
            field_name = field.remote_field.object_id_field_name
        # Special handling for many to many relations/fields
        elif field.many_to_many:
            if not isinstance(field, ManyToManyRel):  # Forward relation
                field_name = field.m2m_field_name()
            else:  # Reverse relation
                field_name = field.remote_field.m2m_reverse_field_name()

        setattr(obj, field_name, value)

        if resolve_inconsistencies := getattr(obj, "resolve_inconsistencies", None):
            obj = resolve_inconsistencies(commit=False)

        if not dry_run:
            obj.save()
        else:
            print(
                f"Setting ({type(obj).__name__}-{obj.pk}).{field_name} = "
                f"{type(value).__name__}-{value.pk if hasattr(value, 'pk') else value}"
            )

        return obj

    def _handle_deprecation(
        deprecation: MergeStrategy.RelationDeprecation | None,
        obj: Model,
        field: FieldOrRel,
    ):
        match deprecation:
            case MergeStrategy.RelationDeprecation.ORPHAN:
                if not dry_run:
                    _set_resolve_save(obj, field, None)
                else:
                    print(f"Orphaning {obj} due to deprecation strategy.")
            case MergeStrategy.RelationDeprecation.DELETE:
                if not dry_run:
                    obj.delete()
                else:
                    print(f"Deleting {obj} due to deprecation strategy.")
            case None:
                pass

    for field, strategy in field_strategies.items():
        if isinstance(field, Field) and field.primary_key:
            continue  # Never merge primary keys

        _, from_vals = resolve_field_value(object_from, field, use_display=False)
        _, to_vals = resolve_field_value(object_to, field, use_display=False)

        retainment, deprecation = strategy.to_tuple()

        # Replace is like KEEP but with swapped values,
        # and acts the same for single- and multi-valued fields
        if retainment == MergeStrategy.FieldRetainment.REPLACE:
            to_vals, from_vals = from_vals, to_vals
        elif retainment == MergeStrategy.FieldRetainment.COMBINE:
            # Combine is like KEEP but with added values from "from" that are not in "to"
            to_vals = list(set(to_vals) | set(from_vals))

        is_X_to_one = not (field.many_to_many or field.one_to_many)
        if is_X_to_one and len(to_vals) != 1:
            raise ValueError(
                f"Field {field.name} admits single values but received many: {to_vals}"
            )

        if not field.is_relation:
            _set_resolve_save(object_to, field, to_vals[0])
            # Deprecation guaranteed to be None for non-relational fields
        elif field.many_to_one:
            # Many to one is a forward foreign key, just set it,
            # and apply deprecation on the other afterwards(!)
            _handle_deprecation(deprecation, object_from, field)
            _set_resolve_save(object_to, field, to_vals[0])
        elif field.one_to_many:
            # One to many is a reverse foreign key, so we need to set the remote field on the related objects
            for from_val in from_vals:
                _handle_deprecation(deprecation, from_val, field.remote_field)
            for to_val in to_vals:
                _set_resolve_save(to_val, field.remote_field, object_to)

        elif field.many_to_many:
            through_model = None
            if isinstance(field, ManyToManyField):  # Forward relation
                m2m_field_name = field.m2m_field_name()
                through_model = field.remote_field.through
            elif isinstance(field, ManyToManyRel):  # Reverse relation
                # translate field to forward and get its reverse name
                through_model = field.through
                m2m_field_name = field.remote_field.m2m_reverse_field_name()

            if through_model is None:
                raise ValueError("Through model could not be determined.")

            # When accessing the model via the `through` attribute,
            # we get a table with two forward foreign keys. No complications.
            # We do this to get them as objects of the through "invisible" model
            # instead of resolved instances of the related model
            through_from_vals = through_model.objects.filter(
                **{m2m_field_name: object_from}
            )
            through_to_vals = through_model.objects.filter(
                **{m2m_field_name: object_to}
            )

            # Replace is like KEEP but with swapped values,
            # and acts the same for single- and multi-valued fields
            if retainment == MergeStrategy.FieldRetainment.REPLACE:
                through_to_vals, through_from_vals = through_from_vals, through_to_vals
            elif retainment == MergeStrategy.FieldRetainment.COMBINE:
                # Combine is like KEEP but with added values from "from" that are not in "to"
                through_to_vals = list(set(through_to_vals) | set(through_from_vals))

            for through_from_val in through_from_vals:
                _handle_deprecation(deprecation, through_from_val, field)
            for through_to_val in through_to_vals:
                _set_resolve_save(through_to_val, field, object_to)

        elif field.one_to_one:
            # One to one is a special case of many to one, and we
            # can't know off the bat if it is forward or reverse.

            if field.auto_created:  # Implies reverse FK.
                field_name = get_field_name(field)

                # Translate the objects from reverse FK to forward FK
                #! There could be a complication here as I used to manipulate
                #! fields and their values, but now I'm manipulating fields twice
                #! Make sure the logic is bulletproof.
                forward_object_to = getattr(object_to, field_name)
                forward_object_from = getattr(object_from, field_name)

                # Below this line, the procedure is identical by making the substitutions
                # `object_X` -> `forward_object_X` and
                # `field` -> `remote_field`
                # if not for the fact that deprecation runs first.
                # In all examples, however, the deprecation could be made to run first
                #! Double check this.

                merge_objects(
                    forward_object_from,
                    forward_object_to,
                    {field.remote_field: strategy},
                    dry_run=dry_run,
                )

            else:  # Forward FK, like many-to-one FFK.
                _handle_deprecation(deprecation, object_from, field)
                _set_resolve_save(object_to, field, to_vals[0])

        else:
            raise ValueError("Field type not supported for merging.")
