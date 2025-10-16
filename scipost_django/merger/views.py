__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest
from django.db.models import Model
from django.db.models.fields.generated import GeneratedField
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from scipost.permissions import HTMXPermissionsDenied, HTMXResponse

from .models import NonDuplicateMark, MergeHistoryRecord
from .utils import (
    M,
    FieldOrRel,
    FieldValues,
    resolve_field_value,
    merge_objects,
    MergeChangeType,
    MergeStrategy,
)

from typing import Any


class BaseComparisonView(PermissionRequiredMixin, TemplateView):
    """
    Abstract view for dealing with comparisons of two objects of the same content type.
    """

    permission_required = "scipost.can_compare_objects"
    content_type_kwarg = "content_type"
    object_a_kwarg = "object_a_pk"
    object_b_kwarg = "object_b_pk"

    def get_permission_required(self) -> list[str]:
        perms = list(super().get_permission_required())

        # Check `can_compare_<model_name_plural>` permission for the content type.
        if model := self.get_content_type().model_class():
            perms += [f"scipost.can_compare_{model._meta.verbose_name_plural}"]

        return perms

    def _get_param(self, param: str) -> str:
        """
        Search for a parameter in the URL kwargs, GET parameters, and POST parameters.
        Optionally, convert to int if it is a digit.
        """
        return (
            self.kwargs.get(param, "")
            or self.request.GET.get(param, "")
            or self.request.POST.get(param, "")
        )

    def get_content_type(self):
        """
        Retrieve the content type for the comparison based on the view's `content_type_kwarg` variable.

        Returns the content type object.

        Raises:
        - BadRequest if no content type was provided.
        - ValueError if no content type could be resolved.
        """
        content_type_str = self._get_param(self.content_type_kwarg)

        if not content_type_str:
            raise BadRequest("No content type provided.")

        content_type: "ContentType | None" = None
        if content_type_str.isdigit():
            content_type_id = int(content_type_str)
            content_type = ContentType.objects.filter(id=content_type_id).first()
        else:
            content_type = (
                ContentType.objects.filter(model__iexact=content_type_str)
                .order_by("app_label")
                .first()
            )

        if content_type is None:
            raise ValueError("No content type could be resolved.")

        return content_type

    def get_objects(self):
        """
        Retrieve the two objects to be compared, according to the view's variables:
        - content_type_kwarg (default: "content_type_id")
        - object_a_kwarg (default: "object_a_pk")
        - object_b_kwarg (default: "object_b_pk")

        Returns a tuple of the two objects.
        """

        if not (content_type := self.get_content_type()):
            raise BadRequest("No content type resolved.")
        if not (object_a_pk := self._get_param(self.object_a_kwarg)):
            raise BadRequest("No object A PK provided.")
        if not (object_b_pk := self._get_param(self.object_b_kwarg)):
            raise BadRequest("No object B PK provided.")

        try:
            object_a = content_type.get_object_for_this_type(pk=object_a_pk)
            object_b = content_type.get_object_for_this_type(pk=object_b_pk)
        except Exception as e:
            raise Http404(f"Error: {e}")

        return object_a, object_b

    def get_non_duplicate_declaration(
        self, object_a: M, object_b: M
    ) -> NonDuplicateMark | None:
        """
        Retrieve all NonDuplicateMark declarations for the two objects.
        """
        try:
            content_type = self.get_content_type()
        except (BadRequest, Http404, KeyError):
            return None

        # Ensure object_a.pk < object_b.pk
        if object_a.pk > object_b.pk:
            object_a, object_b = object_b, object_a

        return NonDuplicateMark.objects.filter(
            content_type_id=content_type.id,
            object_a_pk=object_a.pk,
            object_b_pk=object_b.pk,
        ).first()

    def get_object_field_data(
        self, object: Model, use_display: bool = True
    ) -> dict[FieldOrRel, tuple[str, FieldValues]]:
        """
        Return a list of fields, ordered by type (fields, Any-to-1 and 1-to-Any relations).
        """

        def _sort_field_on_type(field: FieldOrRel) -> int:
            """Sort fields by type:
            - fields
            - 1-to-1 and many-to-1,
            - 1-to-many and many-to-many.
            """
            if field.is_relation:
                if field.many_to_many or field.one_to_many:
                    return 2
                else:
                    return 1
            return 0

        model_fields = object._meta.get_fields(
            include_parents=True, include_hidden=False
        )

        model_fields = sorted(model_fields, key=_sort_field_on_type)

        resolved_fields = {}
        for field in model_fields:
            field.merge_strategies = MergeStrategy.get_admissible_strategies(field)
            field.selected_strategy = MergeStrategy.default_for_field(field)

            # We don't care about GeneratedFields or "calculated fields" (cf_)
            if isinstance(field, GeneratedField) or field.name.startswith("cf_"):
                continue

            resolved_fields[field] = resolve_field_value(
                object, field, use_display=use_display
            )

        return resolved_fields


class PotentialDuplicatesView(BaseComparisonView):
    permission_required = "scipost.can_compare_objects"

    def get_template_names(self) -> list[str]:
        if self.request.headers.get("HX-Request") == "true":
            return ["merger/_hx_potential_duplicates_selector.html"]
        return ["merger/potential_duplicates.html"]

    def get_push_url(self):
        """
        Construct a URL to push to the browser history.
        It contains the content type, and optionally the group, object_a_pk, and object_b_pk.
        """
        content_type = self.get_content_type()

        group = self._get_param("group")
        object_a, object_b = self.get_objects()

        if not group:
            return reverse_lazy(
                "merger:duplicates",
                args=[content_type.model],
            )

        if not (object_a.pk and object_b.pk):
            return reverse_lazy(
                "merger:duplicates",
                args=[content_type.model, group],
            )

        return reverse_lazy(
            "merger:duplicates",
            args=[content_type.model, group, object_a.pk, object_b.pk],
        )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        dispatch = super().dispatch(request, *args, **kwargs)

        try:
            push_url = self.get_push_url()
        except (BadRequest, Http404, KeyError):
            push_url = None

        if push_url and request.headers.get("HX-Request") == "true":
            dispatch["HX-Push-Url"] = push_url

        return dispatch

    def get_objects(self):
        potential_duplicates = self.get_potential_duplicates()

        selected_group = self.get_or_infer_group(potential_duplicates)
        selected_group_duplicates = {
            str(duplicate.pk): duplicate
            for duplicate in potential_duplicates.get(selected_group or "", [])
            if duplicate.pk
        }

        object_a_pk = self._get_param("object_a_pk")
        object_b_pk = self._get_param("object_b_pk")

        # Automatically select the first two objects in the group if
        # no selection is made by the user or if the selected objects
        # are no longer part of the selected group (change of group).
        if len(selected_group_duplicates) >= 2 and not (
            object_a_pk in selected_group_duplicates
            and object_b_pk in selected_group_duplicates
        ):
            pks = list(selected_group_duplicates.keys())
            object_a_pk = pks[0]
            object_b_pk = pks[1]

        object_a = selected_group_duplicates[object_a_pk]
        object_b = selected_group_duplicates[object_b_pk]

        return object_a, object_b

    def get_potential_duplicates(self) -> dict[str, list[Model]]:
        model = self.get_model()
        potential_duplicates: dict[str, list[Model]] = {}
        try:
            potential_duplicates = model.objects.get_potential_duplicates()  # type: ignore
        except AttributeError:
            raise BadRequest("This model does not support duplicate detection.")
        return potential_duplicates

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        content_type = self.get_content_type()
        model = self.get_model()

        potential_duplicates = self.get_potential_duplicates()

        selected_group = self.get_or_infer_group(potential_duplicates)
        selected_group_duplicates = potential_duplicates.get(selected_group or "", [])

        try:
            object_a, object_b = self.get_objects()
            non_duplicate_declaration = self.get_non_duplicate_declaration(
                object_a, object_b
            )
        except (BadRequest, Http404, KeyError):
            object_a, object_b = None, None
            non_duplicate_declaration = None

        context |= {
            "content_type": content_type,
            "object_a": object_a,
            "object_b": object_b,
            "model_name": model._meta.verbose_name,
            "model_name_plural": model._meta.verbose_name_plural,
            "potential_duplicates": potential_duplicates,
            "selected_group": selected_group,
            "selected_group_duplicates": selected_group_duplicates,
            "non_duplicate_declaration": non_duplicate_declaration,
        }

        return context

    def get_or_infer_group(
        self, potential_duplicates: dict[str, list[Model]]
    ) -> str | None:
        """Infer the group if not provided in the URL parameters."""
        if group := self._get_param("group"):
            return group

        object_a_pk = self._get_param("object_a_pk")
        object_b_pk = self._get_param("object_b_pk")

        for group, duplicates in potential_duplicates.items():
            pks = {str(dup.pk) for dup in duplicates if dup.pk}
            if object_a_pk in pks and object_b_pk in pks:
                return group

    def get_model(self):
        content_type = self.get_content_type()
        model = content_type.model_class()
        if not model:
            raise BadRequest("No model could be resolved for this content type.")
        return model


class HXCompareView(BaseComparisonView):
    """
    Side-by-side comparison of two objects of the same content type.
    """

    template_name = "merger/_hx_compare.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        content_type = self.get_content_type()

        try:
            object_a, object_b = self.get_objects()
            non_duplicate_declaration = self.get_non_duplicate_declaration(
                object_a, object_b
            )
        except (BadRequest, Http404, KeyError):
            return {"content_type": content_type}

        context |= {
            "content_type": content_type,
            "objects": [object_a, object_b],
            "object_a": object_a,
            "object_b": object_b,
            "non_duplicate_declaration": non_duplicate_declaration,
        }

        if model := content_type.model_class():
            obj_a_field_groups = self.get_object_field_data(object_a)
            obj_b_field_groups = self.get_object_field_data(object_b)

            object_field_values = {
                field: (object_a_val, object_b_val)
                for (field, (_, object_a_val)), (_, (_, object_b_val)) in zip(
                    obj_a_field_groups.items(), obj_b_field_groups.items()
                )
            }

            context |= {
                "model_name": model._meta.verbose_name,
                "model_name_plural": model._meta.verbose_name_plural,
                "object_field_values": object_field_values,
            }

        return context


class HXNonDuplicateMarkCreateView(BaseComparisonView):
    """
    View for creating a NonDuplicateMark object.
    """

    permission_required = "scipost.can_mark_non_duplicates"

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.headers.get("HX-Request") != "true":
            raise BadRequest("This view is only accessible via HTMX.")

        if not request.user.has_perm("scipost.can_mark_non_duplicates"):
            return HTMXPermissionsDenied(
                "You do not have permission to mark non-duplicates."
            )

        NonDuplicateMark.objects.bulk_create(
            NonDuplicateMark.from_objects(
                *self.get_objects(),
                marked_by=request.user.contributor,
                description=request.headers.get("HX-Prompt"),
            )
        )

        return HTMXResponse(
            "Objects marked as non-duplicates.",
            tag="success",
        )


class HXMergeView(BaseComparisonView):
    """
    If GET: Display a "diff" view of the two objects, with buttons to merge them.
    If POST: Merge the two objects, keeping a record of the merge in the database.
    """

    template_name = "merger/merge.html"
    permission_required = "scipost.can_merge_objects"

    @staticmethod
    def compute_field_merge_changes(
        field: FieldOrRel,
        from_vals: FieldValues,
        to_vals: FieldValues,
        strategy: MergeStrategy | None = None,
    ) -> list[tuple[MergeChangeType, Model | None]]:
        """
        Produces a preview of what the merged field will look like.
        Return a list of tuples, where the first element is the status of the object (unchanged, added, removed)
        """
        strategy = strategy or MergeStrategy.default_for_field(
            field, from_vals, to_vals
        )

        changes: list[tuple[MergeChangeType, Model | None]] = []

        if (
            (not field.is_relation or field.one_to_one or field.many_to_one)
            and (from_val := next(iter(from_vals), None))
            and (to_val := next(iter(to_vals), None))
        ):
            match strategy.to_tuple():
                case (MergeStrategy.FieldRetainment.KEEP, deprecation_strategy):
                    merge_change_type = (
                        deprecation_strategy.merge_change_type
                        if deprecation_strategy
                        else MergeChangeType.REMOVED
                    )
                    if from_val == to_val or not from_val:  # Empty "from" or identical
                        changes = [(MergeChangeType.UNCHANGED, to_val)]
                    elif not to_val:  # Empty "to" value, so "from" value prevails
                        changes = [(MergeChangeType.ADDED, from_val)]
                    elif from_val:  # Non-empty "from" removed and "to" unchanged
                        changes = [
                            (merge_change_type, from_val),
                            (MergeChangeType.UNCHANGED, to_val),
                        ]
                case (MergeStrategy.FieldRetainment.REPLACE, deprecation_strategy):
                    merge_change_type = (
                        deprecation_strategy.merge_change_type
                        if deprecation_strategy
                        else MergeChangeType.REMOVED
                    )
                    if from_val == to_val:  # Same value, just appear unchanged
                        changes = [(MergeChangeType.UNCHANGED, to_val)]
                    elif not from_val:  # Empty "from" value, so "to" value prevails
                        changes = [(MergeChangeType.UNCHANGED, to_val)]
                    elif to_val:  # Overwrite "to" value with "from" value
                        changes = [
                            (merge_change_type, to_val),
                            (MergeChangeType.ADDED, from_val),
                        ]
                case _:
                    raise NotImplementedError(
                        f"Merge strategy {strategy} not implemented for single-valued fields."
                    )
        elif field.many_to_many or field.one_to_many:
            retainment, deprecation = strategy.to_tuple()
            if (
                retainment != MergeStrategy.FieldRetainment.COMBINE
                and deprecation is None
            ):
                raise ValueError(
                    "Deprecation strategy must be provided for multi-valued fields."
                )

            match retainment:
                case MergeStrategy.FieldRetainment.KEEP:
                    existing = [(MergeChangeType.UNCHANGED, o) for o in to_vals if o]
                    removed = [
                        (deprecation.merge_change_type, o)
                        for o in set(from_vals) - set(to_vals)
                        if o
                    ]
                    changes = existing + removed
                case MergeStrategy.FieldRetainment.REPLACE:
                    added = [
                        (MergeChangeType.ADDED, o)
                        for o in set(from_vals) - set(to_vals)
                        if o
                    ]
                    existing = [
                        (MergeChangeType.UNCHANGED, o)
                        for o in to_vals
                        if o and o in from_vals
                    ]
                    removed = [
                        (deprecation.merge_change_type, o)
                        for o in set(to_vals) - set(from_vals)
                        if o
                    ]
                    changes = added + removed + existing
                case MergeStrategy.FieldRetainment.COMBINE:
                    existing = [(MergeChangeType.UNCHANGED, o) for o in to_vals if o]
                    added = [
                        (MergeChangeType.ADDED, o)
                        for o in set(from_vals) - set(to_vals)
                        if o
                    ]
                    changes = existing + added
                case _:
                    raise NotImplementedError(
                        f"Merge strategy {strategy} not implemented for multi-valued fields."
                    )

        return sorted(changes, key=lambda c: c[0].name, reverse=True)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        content_type = self.get_content_type()
        object_from, object_to = self.get_objects()
        non_duplicate_declaration = self.get_non_duplicate_declaration(
            object_from, object_to
        )

        context |= {
            "content_type": content_type,
            "objects": [object_from, object_to],
            "object_from": object_from,
            "object_to": object_to,
            "non_duplicate_declaration": non_duplicate_declaration,
        }

        if model := content_type.model_class():
            obj_a_field_data = self.get_object_field_data(object_from)
            obj_b_field_data = self.get_object_field_data(object_to)

            object_field_changes = {
                field: (field_name, changes)
                for (field, (field_name, from_val)), (_, (_, to_val)) in zip(
                    obj_a_field_data.items(), obj_b_field_data.items()
                )
                if (
                    changes := self.compute_field_merge_changes(field, from_val, to_val)
                )
            }

            context |= {
                "model_name": model._meta.verbose_name,
                "model_name_plural": model._meta.verbose_name_plural,
                "object_field_changes": object_field_changes,
            }

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        content_type = self.get_content_type()
        model_class = content_type.model_class()
        object_from, object_to = self.get_objects()

        # request.POST will have a `field_name` array to which we will match the strategies
        field_strategies: dict[FieldOrRel, MergeStrategy] = {
            field: MergeStrategy(strategy)
            for name in request.POST.getlist("field_name")
            if (strategy := request.POST.get(f"field_{name}_strategy"))
            and model_class is not None
            and (field := model_class._meta.get_field(name))
        }

        try:
            merge_history_record = MergeHistoryRecord.from_operation(
                performed_by=request.user.contributor,
                deprecated=object_from,
                kept=object_to,
                options={
                    "strategies": {
                        field.name: [
                            strategy_part.value if strategy_part is not None else None
                            for strategy_part in strategy.to_tuple()
                        ]
                        for field, strategy in field_strategies.items()
                    }
                },
                description=request.headers.get("HX-Prompt", ""),
            )

            merge_objects(object_from, object_to, field_strategies)

            merge_history_record.save()

            # Delete the "from" object unless it favors being kept
            # and "rerouted" via a "duplicate_of" field.
            if hasattr(object_from, "duplicate_of"):
                setattr(object_from, "duplicate_of", object_to)
                object_from.save()
            else:
                object_from.delete()

        except Exception as e:
            messages.error(request, f"Error during merge: {e}")
            redirect_url = request.get_full_path()
        else:
            messages.success(request, "Objects merged successfully.")
            redirect_url = reverse_lazy("merger:duplicates", args=[content_type.model])

        response = HttpResponse()
        response.headers["HX-Redirect"] = redirect_url
        return response


class HXMergePreviewFieldView(HXMergeView):
    """
    View for previewing the merge of a single field.
    """

    permission_required = "scipost.can_compare_objects"
    template_name = "merger/_hx_merge_field.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.headers.get("HX-Request") != "true":
            raise BadRequest("This view is only accessible via HTMX.")

        if not request.user.has_perm("scipost.can_compare_objects"):
            return HTMXPermissionsDenied(
                "You do not have permission to compare objects."
            )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        if not (field_name := self._get_param("field_name")):
            raise BadRequest("No field name provided.")

        if not (
            (strategy_str := self._get_param(f"field_{field_name}_strategy"))
            and (selected_strategy := MergeStrategy(strategy_str))
        ):
            raise BadRequest("No merge strategy provided.")

        content_type = self.get_content_type()

        try:
            field = content_type.model_class()._meta.get_field(field_name)
        except Exception as e:
            raise AttributeError(f"Error retrieving field: {e}")

        field_merge_strategies = MergeStrategy.get_admissible_strategies(field)
        if selected_strategy not in field_merge_strategies:
            raise ValueError("Invalid merge strategy provided for this field.")

        object_from, object_to = self.get_objects()

        try:
            from_val = self.get_object_field_data(object_from)[field][1]
            to_val = self.get_object_field_data(object_to)[field][1]
        except KeyError:
            raise KeyError("Field not found on one of the objects.")

        changes = self.compute_field_merge_changes(
            field, from_val, to_val, selected_strategy
        )

        field.selected_strategy = selected_strategy

        context |= {
            "field": field,
            "from_val": from_val,
            "to_val": to_val,
            "changes": changes,
        }

        return context
