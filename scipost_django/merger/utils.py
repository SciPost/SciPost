import enum

from django.db.models import Model, Field, ForeignObjectRel

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
