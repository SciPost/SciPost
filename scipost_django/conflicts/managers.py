__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class ConflictOfInterestQuerySet(models.QuerySet):
    def unverified(self):
        return self.filter(status='unverified')

    def non_deprecated(self):
        return self.exclude(status='deprecated')

    def filter_for_profile(self, profile):
        """
        Return all instances for certain profile.
        """
        return self.filter(
            models.Q(profile=profile) | models.Q(related_profile=profile)).distinct()
