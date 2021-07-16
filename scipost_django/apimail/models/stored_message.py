__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import pytz
import uuid as uuid_lib

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..managers import StoredMessageQuerySet
from ..storage import APIMailSecureFileStorage
from ..validators import validate_max_email_mime_file_size


MIME_BASE_DIR = "uploads/apimail/mime"

def get_mime_upload_path(instance, filename):
    """
    Set a (likely) unique directory path for each attachment.
    """
    if not isinstance(instance.uuid, uuid_lib.UUID):
        raise FieldError("StoredMessage MIME upload path cannot be determined (uuid not defined).")
    u = str(instance.uuid)
    return f"{MIME_BASE_DIR}/{u[:2]}/{u[2:4]}/{u[4:6]}/{u[6:8]}/{filename}"


class StoredMessage(models.Model):
    """
    Storage class for an email message stored at Mailgun.
    """

    uuid = models.UUIDField( # Used by the API to look up the record
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    data = models.JSONField(default=dict)

    datetimestamp = models.DateTimeField(default=timezone.now)

    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='+')

    tags = models.ManyToManyField(
        'apimail.UserTag',
        blank=True,
        related_name='messages')

    attachment_files = models.ManyToManyField(
        'apimail.AttachmentFile',
        blank=True)

    mime = models.FileField(
        upload_to=get_mime_upload_path,
        validators=[validate_max_email_mime_file_size,],
        storage=APIMailSecureFileStorage(),
        blank=True, null=True
    )

    objects = StoredMessageQuerySet.as_manager()

    class Meta:
        ordering = ['-datetimestamp',]

    def __str__(self):
        return('%s: %s (from %s to %s)' % (
            self.datetimestamp, self.data['subject'][:20], self.data['From'], self.data['To']))

    def get_absolute_url(self):
        return reverse('apimail:message_detail', kwargs={'uuid': self.uuid})

    def get_absolute_url_api(self):
        return reverse('apimail:api_stored_message_retrieve', kwargs={'uuid': self.uuid})
