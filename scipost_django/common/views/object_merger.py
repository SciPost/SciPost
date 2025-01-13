__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest
from django.http import Http404, HttpRequest, HttpResponse
from django.views.generic import TemplateView


class CompareView(TemplateView, PermissionRequiredMixin):
    """
    Abstract view for dealing with comparisons of two objects of the same content type.
    """

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
        perms = super().get_permission_required()

        # Check `can_compare_<model_name_plural>` permission for the content type.
        if model := self.get_content_type().model_class():
            return perms + [f"scipost.can_compare_{model._meta.verbose_name_plural}"]

        return perms
