from django.db import models


class ProceedingQuerySet(models.QuerySet):
    def open_for_submission(self):
        return self.filter(open_for_submission=True)
