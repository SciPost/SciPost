__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class EditorialCommunicationQuerySet(models.QuerySet):
    def for_referees(self):
        """Only return communication between Referees and Editors."""
        return self.filter(comtype__in=["EtoR", "RtoE"])

    def for_authors(self):
        """Only return communication between Authors and Editors."""
        return self.filter(comtype__in=["EtoA", "AtoE"])
