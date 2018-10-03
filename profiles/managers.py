__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Q


class ProfileQuerySet(models.QuerySet):

    def get_unique_from_email_or_None(self, email):
        try:
            return self.get(Q(email=email) | Q(alternativeemail__email=email))
        except self.model.DoesNotExist:
            pass
        except self.model.MultipleObjectsReturned:
            pass
        return self.none()
