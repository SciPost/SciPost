__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import pytz
import uuid as uuid_lib

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..managers import ComposedMessageQuerySet


class ComposedMessage(models.Model):
    """
    An outgoing email message.
    """

    STATUS_DRAFT = "draft"
    STATUS_READY = "ready"
    STATUS_RENDERED = "rendered"
    STATUS_SENT = "sent"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_READY, "Ready for sending"),
        (STATUS_RENDERED, "Rendered"),
        (STATUS_SENT, "Sent"),
    )

    uuid = models.UUIDField(  # Used by the API to look up the record
        db_index=True, default=uuid_lib.uuid4, editable=False
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    created_on = models.DateTimeField(default=timezone.now)

    status = models.CharField(
        max_length=8, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )

    from_account = models.ForeignKey("apimail.EmailAccount", on_delete=models.PROTECT)

    to_recipient = models.EmailField(blank=True)

    cc_recipients = ArrayField(models.EmailField(), blank=True, null=True)

    bcc_recipients = ArrayField(models.EmailField(), blank=True, null=True)

    subject = models.CharField(max_length=256, blank=True)

    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)

    headers_added = models.JSONField(default=dict)

    attachment_files = models.ManyToManyField("apimail.AttachmentFile", blank=True)

    objects = ComposedMessageQuerySet.as_manager()

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return "%s: %s (from %s to %s) [%s]" % (
            self.created_on,
            self.subject[:20],
            self.from_account.email,
            self.to_recipient,
            self.get_status_display(),
        )


class ComposedMessageAPIResponse(models.Model):
    """
    Mailgun API response upon action on ComposedMessage.
    """

    message = models.ForeignKey(
        "apimail.ComposedMessage",
        on_delete=models.CASCADE,
        related_name="api_responses",
    )
    datetime = models.DateTimeField(default=timezone.now)
    status_code = models.PositiveSmallIntegerField()
    json = models.JSONField(default=dict)

    class Meta:
        ordering = ["-datetime"]
