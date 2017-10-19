import datetime

from django.db import models


class ProceedingsQuerySet(models.QuerySet):
    def open_for_submission(self):
        today = datetime.date.today()
        return self.filter(submissions_open__lte=today, submissions_close__gte=today)
