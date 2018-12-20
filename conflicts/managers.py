__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class ConflictOfInterestQuerySet(models.QuerySet):
    def unverified(self):
        return self.filter(status='unverified')

    def non_deprecated(self):
        return self.exclude(status='deprecated')
