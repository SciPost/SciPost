__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import STATUS_UNVERIFIED, STATUS_DEPRECATED


class ConflictOfInterestQuerySet(models.QuerySet):
    def unverified(self):
        return self.filter(status=STATUS_UNVERIFIED)

    def non_deprecated(self):
        return self.exclude(status=STATUS_DEPRECATED)
