__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
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
    The MailLog table is meant as a container of mails.
    Mails are not directly sent, but added to this table first.
    Using a cronjob, the unsent messages are eventually sent using
    the chosen MailBackend.
    """
    processed = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=MAIL_STATUSES, default=MAIL_RENDERED)

    mail_code = models.CharField(max_length=254, blank=True)

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

    def get_full_context(self):
        """Get the full template context needed to render the template."""
        if hasattr(self, '_context'):
            return self._context
        self._context = {}
        for relation in self.context.all():
            self._context[relation.name] = relation.get_item()
        return self._context


class MailLogRelation(models.Model):
    """
    A template context item for the MailLog in case the a mail has delayed rendering.
    This may be plain text or any relation within the database.
    """

    mail = models.ForeignKey('mails.MailLog', on_delete=models.CASCADE, related_name='context')

    name = models.CharField(max_length=254)
    value = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def get_item(self):
        if self.value:
            return self.value
        elif self.content_object:
            return self.content_object
        return None
