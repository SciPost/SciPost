__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class EditorialCommunicationQuerySet(models.QuerySet):
    def for_referees(self):
        """Only return communication related to Referees."""
        return self.filter(comtype__contains="R")

    def for_authors(self):
        """Only return communication related to Authors."""
        return self.filter(comtype__contains="A")
