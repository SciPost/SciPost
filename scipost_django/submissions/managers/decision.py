__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class EditorialDecisionQuerySet(models.QuerySet):
    def deprecated(self):
        return self.filter(status=self.model.DEPRECATED)

    def nondeprecated(self):
        return self.exclude(status=self.model.DEPRECATED)

    def latest_version(self):
        return self.order_by("-version").first()
