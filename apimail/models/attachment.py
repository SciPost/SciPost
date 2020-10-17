__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse

from ..storage import APIMailSecureFileStorage

from ..validators import validate_max_email_attachment_file_size


class AttachmentFile(models.Model):
    """
    File representing an attachment to an email message.
    """

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid_lib.uuid4,
        unique=True,
        editable=False)
    data = JSONField(default=dict)
    file = models.FileField(
        upload_to='uploads/mail/attachments/%Y/%m/%d/',
        validators=[validate_max_email_attachment_file_size,],
        storage=APIMailSecureFileStorage())

    def __str__(self):
        return '%s (%s, %s)' % (self.data['name'], self.data['content-type'], self.file.size)

    def get_absolute_url(self):
        return reverse('apimail:attachment_file',
                       kwargs={'uuid': self.uuid})
