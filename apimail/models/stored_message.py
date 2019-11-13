__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse

from scipost.storage import SecureFileStorage

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

    class Meta:
        ordering = ['-data__Date',]

    def get_absolute_url(self):
        return reverse('apimail:stored_message_detail', kwargs={'uuid': self.uuid})


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
