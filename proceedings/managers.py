__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone

today = timezone.now().date()


class ProceedingsQuerySet(models.QuerySet):
    def open_for_submission(self):
        return self.filter(submissions_open__lte=today, submissions_close__gte=today)
