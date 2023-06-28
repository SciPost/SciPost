__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class QualificationQuerySet(models.QuerySet):
    def qualified(self):
        """
        Filter for Fellows which are at least marginally qualified.
        """
        return self.filter(
            status__in=[
                self.model.STATUS_EXPERT,
                self.model.STATUS_VERY_KNOWLEDGEABLE,
                self.model.STATUS_KNOWLEDGEABLE,
                self.model.STATUS_MARGINALLY_QUALIFIED,
            ]
        )

    def not_qualified(self):
        return self.filter(
            status__in=[
                self.model.STATUS_NOT_REALLY_QUALIFIED,
                self.model.STATUS_NOT_AT_ALL_QUALIFIED,
            ]
        )
