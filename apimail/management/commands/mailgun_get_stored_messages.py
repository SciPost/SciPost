__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from tempfile import TemporaryFile

import requests

from django.conf import settings
from django.core.files import File
from django.core.management import BaseCommand

from ...exceptions import APIMailError
from ...models import Event, StoredMessage, StoredMessageAttachment


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
                # Now deal with attachments
                for att_item in response['attachments']:
                    with TemporaryFile() as tf:
                        r = requests.get(att_item['url'], stream=True)
                        for chunk in r.iter_content(chunk_size=8192):
                            tf.write(chunk)
                        tf.seek(0)
                        sma = StoredMessageAttachment.objects.create(
                            message=sm, data=att_item)
                        sma._file.save(att_item['name'], File(tf))
