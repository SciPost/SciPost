__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class PetitionSignatoryQuerySet(models.QuerySet):
    def verified(self):
        return self.filter(verified=True)

    def unverified(self):
        return self.filter(verified=False)
