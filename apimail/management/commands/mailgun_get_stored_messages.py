__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.core.management import BaseCommand

from ...exceptions import APIMailError
from ...models import Event, StoredMessage


class Command(BaseCommand):
    """
    For all Events which do not have a related StoredMessage,
    GET the latter from Mailgun API and save it to the DB.
    """

    help = 'Gets stored messages from the Mailgun API and saves them to the DB.'

    def handle(self, *args, **kwargs):
        orphaned_events = Event.objects.filter(
            stored_message__isnull=True,
            data__event__in=[Event.TYPE_ACCEPTED, Event.TYPE_STORED])
        for orphan in orphaned_events.all():
            response = requests.get(
                orphan.data['storage']['url'],
                auth=("api", settings.MAILGUN_API_KEY)
            ).json()
            if not StoredMessage.objects.filter(
                data__contains={'message-id': orphan.data['message']['headers']['message-id']}
            ).exists():
                sm = StoredMessage.objects.create(data=response)
                orphan.stored_message = sm
                orphan.save()
