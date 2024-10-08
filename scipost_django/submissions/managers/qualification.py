__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class QualificationQuerySet(models.QuerySet):
    def qualified(self):
        """
        Filter for Fellows which are at least marginally qualified.
        """
        return self.filter(
            expertise_level__in=[
                self.model.EXPERT,
                self.model.VERY_KNOWLEDGEABLE,
                self.model.KNOWLEDGEABLE,
                self.model.MARGINALLY_QUALIFIED,
            ]
        )

    def not_qualified(self):
        return self.filter(
            expertise_level__in=[
                self.model.NOT_REALLY_QUALIFIED,
                self.model.NOT_AT_ALL_QUALIFIED,
            ]
        )
