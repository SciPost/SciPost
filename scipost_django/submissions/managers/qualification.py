__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class QualificationQuerySet(models.QuerySet):
    def qualified(self):
        """
        Filter for Fellows which are at least marginally qualified.
        """
        return self.filter(expertise_level__in=self.model.EXPERTISE_QUALIFIED)

    def not_qualified(self):
        return self.filter(expertise_level__in=self.model.EXPERTISE_NOT_QUALIFIED)
