from django.db import models

from .constants import MAIL_LIST_STATUS_ACTIVE


class MailListManager(models.Manager):
    def active(self):
        return self.filter(status=MAIL_LIST_STATUS_ACTIVE)
