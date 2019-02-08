__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class FunderQuerySet(models.QuerySet):
    def has_publications(self):
        """Return those Funder instances related to any Publication instance."""
        return self.filter(
            models.Q(publications__isnull=False) | models.Q(grants__publications__isnull=False))
