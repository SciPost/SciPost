__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse


class Event(models.Model):
    """
    Storage class for a Mailgun event.

    Mailgun events are harvested through GET requests (rather than through webhooks).
    Since they have a loose structure, the data is stored in a simple JSONField.
    """
    uuid = models.UUIDField( # Used by the API to look up the record
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    data = JSONField(default=dict)

    def get_absolute_url(self):
        return reverse('apimail:event_detail', kwargs={'uuid': self.uuid})
