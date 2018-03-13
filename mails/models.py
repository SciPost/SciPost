from django.db import models
from django.contrib.postgres.fields import ArrayField

from .managers import MailLogQuerySet


class MailLog(models.Model):
    """
    The MailLog table is meant as a container of mails. Mails are not directly send, but first
    added to this table. Using a cronjob, the unsend messages are really being send using
    the chosen MailBackend.
    """
    processed = models.BooleanField(default=False)

    body = models.TextField()
    body_html = models.TextField(blank=True)

    to_recipients = ArrayField(
        models.EmailField(),
        blank=True, null=True)
    bcc_recipients = ArrayField(
        models.EmailField(),
        blank=True, null=True)

    from_email = models.CharField(max_length=254, blank=True)
    subject = models.CharField(max_length=254, blank=True)

    objects = MailLogQuerySet.as_manager()

    def __str__(self):
        return '{id}. {subject} ({count} recipients)'.format(
            id=self.id,
            subject=self.subject[:30],
            count=len(self.to_recipients) + len(self.bcc_recipients))
