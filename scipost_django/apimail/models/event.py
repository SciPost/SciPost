__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid as uuid_lib

from django.db import models
from django.urls import reverse


class Event(models.Model):
    """
    Storage class for a Mailgun event.

    Mailgun events are harvested through GET requests (rather than through webhooks).
    Since they have a loose structure, the data is stored in a simple JSONField.
    """
    # We put these constants here for convenience, though they are not used in the model's fields
    TYPE_ACCEPTED = 'accepted'
    TYPE_REJECTED = 'rejected'
    TYPE_DELIVERED = 'delivered'
    TYPE_FAILED = 'failed'
    TYPE_OPENED = 'opened'
    TYPE_CLICKED = 'clicked'
    TYPE_UNSUBSCRIBED = 'unsubscribed'
    TYPE_COMPLAINED = 'complained'
    TYPE_STORED = 'stored'

    uuid = models.UUIDField( # Used by the API to look up the record
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)
    data = models.JSONField(default=dict)
    stored_message = models.ForeignKey(
        'apimail.StoredMessage',
        blank=True, null=True,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-data__timestamp',]

    def __str__(self):
        return('%s: %s -- %s' % (
            self.data['timestamp'],
            self.data['message']['headers']['message-id'],
            self.data['event'],))

    def get_absolute_url(self):
        return reverse('apimail:event_detail', kwargs={'uuid': self.uuid})
