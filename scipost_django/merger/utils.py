import enum
import itertools

from django.contrib.contenttypes.fields import GenericRel
from django.db import transaction
from django.db.models import (
    ManyToManyField,
    ManyToManyRel,
    Model,
    Field,
    ForeignObjectRel,
    UniqueConstraint,
)

from typing import Any, TypeVar


FieldValue = Model | None
FieldOrRel = Field[Any, Any] | ForeignObjectRel
T = TypeVar("T")
M = TypeVar("M", bound=Model)
N = TypeVar("N", bound=Model)


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
) -> tuple[str, list[FieldValue]]:
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

    def _get_field_value(self, field: FieldOrRel, obj: Model) -> list[FieldValue]:
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
    def get_admissible_strategies(
        cls,
        field: FieldOrRel,
        from_vals: list[FieldValue] | None = None,
        to_vals: list[FieldValue] | None = None,
    ) -> tuple[list["MergeStrategy"], "MergeStrategy"]:
        """
        Returns the admissible strategies for a given field, based on its type.
        If values are provided, the preferred strategy will be adjusted accordingly,
        e.g. if KEEP is default but the value is None, REPLACE will be chosen instead.
        """
        admissible_strategies: list[MergeStrategy] = []
        preferred_deprecation_strategy = cls.RelationDeprecation.DELETE

        ##### Add anything that is remotely possible
        if not field.is_relation:
            admissible_strategies.extend((cls.KEEP, cls.REPLACE))

        if field.many_to_many or field.one_to_many:
            admissible_strategies.append(cls.COMBINE)

        if field.is_relation:
            nullable = not field.auto_created and field.null
            remote_nullable = field.auto_created and field.remote_field.null
            if nullable or remote_nullable:
                admissible_strategies.extend((cls.KEEP_ORPHAN, cls.REPLACE_ORPHAN))
                preferred_deprecation_strategy = cls.RelationDeprecation.ORPHAN
            admissible_strategies.extend((cls.KEEP_DELETE, cls.REPLACE_DELETE))

        ##### Determine the preferred strategy based on the field type and values
        # Easy case, *-to-many relations should be combined.
        if field.many_to_many or field.one_to_many:
            return admissible_strategies, cls.COMBINE

        # For *-to-one relations, we have to check if the values are None
        # and return the least-invasive deprecation strategy
        if field.one_to_one or field.many_to_one:
            if not from_vals or all(not v for v in from_vals):
                preferred_retention_strategy = cls.FieldRetainment.KEEP
            elif not to_vals or all(not v for v in to_vals):
                preferred_retention_strategy = cls.FieldRetainment.REPLACE
            else:
                preferred_retention_strategy = cls.FieldRetainment.KEEP

            return admissible_strategies, cls.from_tuple(
                (preferred_retention_strategy, preferred_deprecation_strategy)
            )

        # For single-valued fields just return the self-explanatory default
        if not from_vals or all(not v for v in from_vals):
            preferred_strategy = cls.KEEP
        elif not to_vals or all(not v for v in to_vals):
            preferred_strategy = cls.REPLACE
        # ... but if both are None, no strategy matters, just return KEEP as a default
        else:
            preferred_strategy = cls.KEEP

        return admissible_strategies, preferred_strategy


@transaction.atomic
def merge_objects(
    object_from: M,
    object_to: M,
    field_strategies: dict[FieldOrRel, MergeStrategy],
    dry_run: bool = False,
) -> None:
    def _set_resolve_save(
        obj: N,
        field: FieldOrRel,
        value: Any,
    ) -> N:
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
                f'Setting {type(obj).__name__}({obj.pk}).{field_name} = "{value}"'
                f"\t[{type(value).__name__}({getattr(value, 'pk', value)})]"
            )

        return obj


    def _handle_deprecation(
        obj: M,
        field: FieldOrRel,
        deprecation: MergeStrategy.RelationDeprecation | None,
    ):
        """
        Disassociate the values of the given field from the object, according to the deprecation strategy.
        - ORPHAN: Set the field to None (requires null=True)
        - DELETE: Delete the related objects
        - None: Do nothing
        """
        match deprecation:
            case MergeStrategy.RelationDeprecation.ORPHAN:
                _set_resolve_save(obj, field, None)
            case MergeStrategy.RelationDeprecation.DELETE:
                _, values = resolve_field_value(obj, field, use_display=False)
                for value in values:
                    if value is not None:
                        if not dry_run:
                            value.delete()
                        else:
                            print(
                                f'Deleting {type(value).__name__}({value.pk}) "{value}" due to deprecation strategy.'
                            )
            case None:
                pass

    for field, strategy in field_strategies.items():
        if isinstance(field, Field) and field.primary_key:
            continue  # Never merge primary keys

        _, from_vals = resolve_field_value(object_from, field, use_display=False)
        _, to_vals = resolve_field_value(object_to, field, use_display=False)

        retainment, deprecation = strategy.to_tuple()

        presiding, deprecated = [], []
        if retainment == MergeStrategy.FieldRetainment.KEEP:
            presiding, deprecated = to_vals, from_vals
        if retainment == MergeStrategy.FieldRetainment.REPLACE:
            presiding, deprecated = from_vals, to_vals
        elif retainment == MergeStrategy.FieldRetainment.COMBINE:
            presiding, deprecated = list(set(from_vals) - set(to_vals)), []

        is_X_to_one = not (field.many_to_many or field.one_to_many)
        if is_X_to_one and len(presiding) != 1:
            raise ValueError(
                f"Field {field.name} admits single values but received many: {presiding}"
            )

        # Accessing presiding[0] is safe due to raise above
        if not field.is_relation:
            # If the field is not a relation, deprecation is not needed
            # However, uniqueness constraints may require us to temporarily discard the field's value on the deprecated object before setting it on the presiding object
            if any(
                field.name in constraint.fields
                for constraint in object_to._meta.constraints
                if isinstance(constraint, UniqueConstraint)
            ):
                _set_resolve_save(object_from, field, field.get_default())
            _set_resolve_save(object_to, field, presiding[0])
        elif field.many_to_one:
            # Many to one is a forward foreign key, just set it,
            # and apply deprecation on the other afterwards(!)
            _handle_deprecation(object_from, field, deprecation)
            _set_resolve_save(object_to, field, presiding[0])
        elif field.one_to_one:
            # One to one is a special case of many to one, and we
            # can't know off the bat if it is forward or reverse.

            # Forward FK, like many-to-one FFK above.
            if not field.auto_created:
                _handle_deprecation(object_from, field, deprecation)
                _set_resolve_save(object_to, field, presiding[0])
                continue

            # Implies reverse FK.
            # Reverse it and handle it like a forward FK.
            # `object` -> `remote_object` and
            # `field` -> `remote_field`
            field_name = get_field_name(field)
            field_descriptor = getattr(field.model, field_name)

            try:
                remote_object_from: FieldValue = getattr(object_from, field_name, None)
            except field_descriptor.RelatedObjectDoesNotExist:
                remote_object_from = None

            try:
                remote_object_to: FieldValue = getattr(object_to, field_name, None)
            except field_descriptor.RelatedObjectDoesNotExist:
                remote_object_to = None

            # F -> T
            # RF -> RT
            # ---------
            # Keep: RT._ = T, Deprecate RF
            # Replace: RF._ = T, Deprecate RT
            if retainment == MergeStrategy.FieldRetainment.KEEP:
                remote_object_pres = remote_object_to
                remote_object_depr = remote_object_from
            elif retainment == MergeStrategy.FieldRetainment.REPLACE:
                remote_object_pres = remote_object_from
                remote_object_depr = remote_object_to
            else:
                raise ValueError(
                    "One-to-one relations cannot be combined, "
                    "as they are inherently single-valued."
                )

            if remote_object_depr is not None:
                _handle_deprecation(remote_object_depr, field.remote_field, deprecation)
            if remote_object_pres is not None:
                _set_resolve_save(remote_object_pres, field.remote_field, object_to)

        elif field.one_to_many:
            # One to many is a reverse foreign key, so we need to set the remote field on the related objects
            for depr_val in deprecated:
                _handle_deprecation(depr_val, field.remote_field, deprecation)
            for pres_val in presiding:
                _set_resolve_save(pres_val, field.remote_field, object_to)

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

            # Determine the fields other than the merged model
            through_model_other_fields = [
                field
                for field in through_model._meta.get_fields()
                if field.name != m2m_field_name and not field.auto_created
            ]

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

            presiding, deprecated = [], []
            if retainment == MergeStrategy.FieldRetainment.KEEP:
                presiding, deprecated = through_to_vals, through_from_vals
            if retainment == MergeStrategy.FieldRetainment.REPLACE:
                presiding, deprecated = through_from_vals, through_to_vals
            elif retainment == MergeStrategy.FieldRetainment.COMBINE:
                # Combine is like KEEP but with added values from "from" that are not in "to"
                # Whether two instances are the same is determined by the values of its `through_model_other_fields`
                field_attnames = ["pk"] + [
                    getattr(field, "attname", field.name)
                    for field in through_model_other_fields
                ]
                unique_instances = {
                    tuple(instance_values): pk
                    for (pk, *instance_values) in itertools.chain(
                        through_from_vals.values_list(*field_attnames),
                        through_to_vals.values_list(*field_attnames),
                    )
                }
                presiding = (through_from_vals | through_to_vals).filter(
                    pk__in=unique_instances.values()
                )

            for depr_val in deprecated:
                _handle_deprecation(depr_val, field, deprecation)
            for pres_val in presiding:
                _set_resolve_save(pres_val, field, object_to)

        else:
            raise ValueError("Field type not supported for merging.")
