__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class EditorialDecisionQuerySet(models.QuerySet):
    def latest_version(self):
        return self.order_by("-version").first()
