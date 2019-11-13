__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse


class StoredMessage(models.Model):
    """
    Storage class for an email message stored at Mailgun.
    """
    uuid = models.UUIDField( # Used by the API to look up the record
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    data = JSONField(default=dict)

    def get_absolute_url(self):
        return reverse('apimail:stored_message_detail', kwargs={'uuid': self.uuid})
