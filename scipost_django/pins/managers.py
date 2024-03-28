__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NotesQuerySet(models.QuerySet):

    def visible_to(
        self,
        user: User | None = None,
        model: type[models.Model] | None = None,
    ):
        """
        Filter out notes which are not visible to the given user.
        """

        if user is None or not user.is_authenticated:
            # Without specifying a user, only public notes are visible
            return self.filter(visibility=self.model.VISIBILITY_PUBLIC)
        else:
            # Filter non-author users from viewing private notes
            self = self.exclude(
                models.Q(visibility=self.model.VISIBILITY_PRIVATE)
                & ~models.Q(author=user.contributor)
            )

        # Filter out internal notes unless the user has the default "manager"
        # permission for the given object, e.g. "can_manage_subsidies"
        # If no model is given, just filter out all of them
        model_name = str(model._meta.verbose_name).lower() if model else ""
        can_view_internal_notes = f"scipost.can_view_internal_{model_name}_notes"

        if not (model and user.has_perm(can_view_internal_notes)):
            self = self.exclude(visibility=self.model.VISIBILITY_INTERNAL)

        return self

    def for_object(self, content_type, object_id):
        """
        Filter notes for a given object.
        """
        return self.filter(
            regarding_content_type=content_type,
            regarding_object_id=object_id,
        )

    def visible_for(self, user, content_type, object_id):
        """
        Filter notes for a given object, accessible to the given user.
        """
        model = ContentType.objects.get_for_id(content_type).model_class()
        return self.for_object(content_type, object_id).visible_to(user, model)
