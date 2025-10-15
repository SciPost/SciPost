__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest
from django.db.models import Model
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .models import NonDuplicateMark
from .utils import M

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
