__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.core.exceptions import FieldError
from django.db import models
from django.urls import reverse

from ..storage import APIMailSecureFileStorage

from ..validators import validate_max_email_attachment_file_size

ATT_BASE_DIR = "uploads/apimail/attachments"

def get_attachment_upload_path(instance, filename):
    """
    Set a (likely) unique directory path for each attachment.
    """
    if not isinstance(instance.uuid, uuid_lib.UUID):
        raise FieldError("AttachmentFile upload path cannot be determined (uuid not defined).")
    u = str(instance.uuid)
    return f"{ATT_BASE_DIR}/{u[:2]}/{u[2:4]}/{u[4:6]}/{u[6:8]}/{filename}"


class AttachmentFile(models.Model):
    """
    File representing an attachment to an email message.
    """

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid_lib.uuid4,
        unique=True,
        editable=False)

    data = models.JSONField(default=dict)

    file = models.FileField(
        upload_to=get_attachment_upload_path,
        validators=[validate_max_email_attachment_file_size,],
        storage=APIMailSecureFileStorage())

    sha224_hash = models.CharField(
        max_length=56,
        blank=True,
        help_text='Automatically computed SHA2 (sha224) hash. Used for deduping.')

    def __str__(self):
        return '%s (%s, %s)' % (self.data['name'], self.data['content-type'], self.file.size)

    def get_absolute_url(self):
        return reverse('apimail:attachment_file',
                       kwargs={'uuid': self.uuid})

    @property
    def uuid_01_23_directory_path(self):
        """
        Returns the full path of the first two (of 4) uuid-letter-pair-labelled directories.
        """
        uuid_01 = str(self.uuid)[0:2]
        uuid_23 = str(self.uuid)[2:4]
        part0, part1, part2 = self.file.path.partition(f"{ATT_BASE_DIR}/{uuid_01}/{uuid_23}/")
        path = part0 + part1
        # Safety, in case file has been moved from standard location
        if f"{ATT_BASE_DIR}/{uuid_01}/{uuid_23}/" in path:
            return path
        return self.file.path.rpartition('/')[0]
