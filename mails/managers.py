from django.db import models


class MailLogQuerySet(models.QuerySet):
    def unprocessed(self):
        return self.filter(processed=False)
