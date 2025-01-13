__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import Any, TypeVar
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest
from django.db.models import Model, QuerySet, Field, ForeignObjectRel
from django.http import Http404, HttpRequest, HttpResponse
from django.views.generic import TemplateView

FieldValue = Model | list[Model] | None
FieldOrRel = Field[Any, Any] | ForeignObjectRel
T = TypeVar("T")


class CompareView(PermissionRequiredMixin, TemplateView):
    """
    Abstract view for dealing with comparisons of two objects of the same content type.
    """

    permission_required = "scipost.can_compare_objects"
    content_type_kwarg = "content_type_id"
    object_a_kwarg = "object_a_id"
    object_b_kwarg = "object_b_id"

    def get_content_type(self):
        """
        Retrieve the content type for the comparison based on the view's `content_type_kwarg` variable.

        Returns the content type object.

        Raises:
        - BadRequest if no content type ID is provided.
        - Http404 if the content type with the provided ID is not found.
        """
        content_type_id = self.kwargs.get(self.content_type_kwarg)

        if not content_type_id:
            raise BadRequest("No content type ID provided.")

        try:
            return ContentType.objects.get_for_id(content_type_id)
        except ContentType.DoesNotExist:
            raise Http404(f"Content type with ID {content_type_id} not found.")

    def get_objects(self):
        """
        Retrieve the two objects to be compared, according to the view's variables:
        - content_type_kwarg (default: "content_type_id")
        - object_a_kwarg (default: "object_a_id")
        - object_b_kwarg (default: "object_b_id")

        Returns a tuple of the two objects.
        """
        content_type = self.get_content_type()

        if not (object_a_id := self.kwargs.get(self.object_a_kwarg)):
            raise BadRequest("No object A ID provided.")
        if not (object_b_id := self.kwargs.get(self.object_b_kwarg)):
            raise BadRequest("No object B ID provided.")

        try:
            object_a = content_type.get_object_for_this_type(pk=object_a_id)
            object_b = content_type.get_object_for_this_type(pk=object_b_id)
        except Exception as e:
            raise Http404(f"Error: {e}")

        return object_a, object_b

    def get_permission_required(self) -> list[str]:
        perms = list(super().get_permission_required())

        # Check `can_compare_<model_name_plural>` permission for the content type.
        if model := self.get_content_type().model_class():
            perms += [f"scipost.can_compare_{model._meta.verbose_name_plural}"]

        return perms

    @staticmethod
    def _resolve_field(
        object: Model, field: Field[Any, Any] | ForeignObjectRel
    ) -> tuple[str, FieldValue]:
        """
        Resolve a field of an object to a displayable format.
        Returns a dictionary of the field and its display name - value pair,
        where `value` is a model instance, a list of model instances, or None.
        """
        display_name = getattr(field, "verbose_name", field.name)

        def get_field_queryset() -> QuerySet[Any]:
            try:
                return getattr(object, field.name).all()
            except AttributeError:
                return getattr(object, field.name + "_set").all()

        def get_field_value(obj: Model, field_name: str):
            if display_func := getattr(obj, f"get_{field_name}_display", None):
                return display_func()

            return getattr(obj, field_name)

        if field.many_to_many:
            field_nameval = display_name, list(get_field_queryset())
        elif field.one_to_many:
            if (related_name := getattr(field, "related_name", None)) and (
                related_manager := getattr(object, related_name)
            ):
                field_nameval = display_name, list(related_manager.all())
            else:
                field_nameval = display_name, list(get_field_queryset())
        elif field.one_to_one:
            try:
                field_nameval = display_name, get_field_value(object, field.name)
            except field.related_model.DoesNotExist:
                field_nameval = display_name, None
        else:
            field_nameval = display_name, get_field_value(object, field.name)

        return field_nameval

    def get_object_field_data(
        self, object: Model
    ) -> dict[FieldOrRel, tuple[str, FieldValue]]:
        """
        Return a list of fields
        """
        model_fields = object._meta.get_fields(
            include_parents=True, include_hidden=False
        )
        resolved_fields = {
            field: self._resolve_field(object, field)
            for field in sorted(model_fields, key=lambda f: f.name)
            if not field.name.startswith("cf_")
        }

        return resolved_fields

    @staticmethod
    def group_fields(field_data: dict[FieldOrRel, T]) -> dict[str, dict[FieldOrRel, T]]:

        groups: dict[str, dict[FieldOrRel, T]] = {
            "fields": {},
            "related_objects_one": {},
            "related_objects_many": {},
        }
        for field, resolved_field in field_data.items():
            if field.is_relation:
                if field.many_to_many or field.one_to_many:
                    groups["related_objects_many"] |= {field: resolved_field}
                else:
                    groups["related_objects_one"] |= {field: resolved_field}
            else:
                groups["fields"] |= {field: resolved_field}

        return groups


class HXCompareView(CompareView):
    """
    Side-by-side comparison of two objects of the same content type.
    Contains buttons to merge the two objects.
    """

    template_name = "common/object_merger/compare.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        content_type = self.get_content_type()
        object_a, object_b = self.get_objects()

        context |= {
            "content_type": content_type,
            "objects": [object_a, object_b],
            "object_a": object_a,
            "object_b": object_b,
        }

        if model := content_type.model_class():
            obj_a_field_groups = self.group_fields(self.get_object_field_data(object_a))
            obj_b_field_groups = self.group_fields(self.get_object_field_data(object_b))

            field_groups = {
                group: {
                    field_name: [a_val, b_val]
                    for (_, (field_name, a_val)), (_, (_, b_val)) in zip(
                        obj_a_field_groups[group].items(),
                        obj_b_field_groups[group].items(),
                    )
                    if a_val != b_val
                }
                for group in obj_a_field_groups.keys()
            }

            context |= {
                "model_name": model._meta.verbose_name,
                "model_name_plural": model._meta.verbose_name_plural,
                "field_groups": field_groups,
            }

        return context


