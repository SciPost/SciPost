__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet, Q

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from merger.models import NonDuplicateMark


class NonDuplicateMarkQuerySet(QuerySet["NonDuplicateMark"]):
    def involving(self, object: Model):
        """
        Return a queryset of NonDuplicateMark instances involving the given object.
        """
        content_type = ContentType.objects.get_for_model(object)
        return self.filter(
            Q(object_a_pk=object.pk) | Q(object_b_pk=object.pk),
            content_type=content_type,
        )
