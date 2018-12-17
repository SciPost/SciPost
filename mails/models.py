__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField

from .managers import MailLogQuerySet

MAIL_NOT_RENDERED, MAIL_RENDERED = 'not_rendered', 'rendered'
MAIL_SENT = 'sent'
MAIL_STATUSES = (
    (MAIL_NOT_RENDERED, 'Not rendered'),
    (MAIL_RENDERED, 'Rendered'),
    (MAIL_SENT, 'Sent'),
)


class MailLog(models.Model):
    """
    The MailLog table is meant as a container of mails. Mails are not directly send, but first
    added to this table. Using a cronjob, the unsend messages are really being send using
    the chosen MailBackend.
    """
    processed = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=MAIL_STATUSES, default=MAIL_RENDERED)

    mail_code = models.CharField(max_length=254, blank=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

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

    created = models.DateTimeField(auto_now_add=True)
    latest_activity = models.DateTimeField(auto_now=True)

    objects = MailLogQuerySet.as_manager()

    def __str__(self):
        return '{id}. {subject} ({count} recipients)'.format(
            id=self.id,
            subject=self.subject[:30],
            count=len(self.to_recipients) + len(self.bcc_recipients))
