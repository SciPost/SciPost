__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from django.utils import timezone

from scipost.storage import SecureFileStorage

from ..managers import StoredMessageQuerySet
from ..validators import validate_max_email_attachment_file_size


class StoredMessage(models.Model):
    """
    Storage class for an email message stored at Mailgun.
    """
    uuid = models.UUIDField( # Used by the API to look up the record
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    data = JSONField(default=dict)
    datetimestamp = models.DateTimeField(default=timezone.now)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='+')

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


class StoredMessageAttachment(models.Model):
    message = models.ForeignKey(
        'apimail.StoredMessage',
        on_delete=models.CASCADE,
        related_name='attachments' # doesn't collide with StoredMessage.data.attachments
    )
    data = JSONField(default=dict)
    _file = models.FileField(
        upload_to='uploads/mail/stored_messages/attachments/%Y/%m/%d/',
        validators=[validate_max_email_attachment_file_size,],
        storage=SecureFileStorage())

    def get_absolute_url(self):
        return reverse('apimail:message_attachment',
                       kwargs={'uuid': self.message.uuid, 'pk': self.id})
