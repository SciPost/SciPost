__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class ForumQuerySet(models.QuerySet):
    def anchors(self):
        """Return only the Forums which do not have a parent."""
        return self.filter(parent_object_id__isnull=True)
