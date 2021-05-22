__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from email.utils import parsedate_to_datetime
from tempfile import TemporaryFile

import requests

from django.conf import settings
from django.core.files import File
from django.core.management import BaseCommand

from ...exceptions import APIMailError
from ...models import (
    AttachmentFile,
    Event,
    StoredMessage)


class Command(BaseCommand):
    """
    For all Events which do not have a related StoredMessage,
    GET the latter from Mailgun API and save it to the DB.
    """

    help = 'Gets stored messages from the Mailgun API and saves them to the DB.'

    def handle(self, *args, **kwargs):
        orphaned_events = Event.objects.filter(stored_message__isnull=True)
        for orphan in orphaned_events.all():
            if orphan.stored_message:
                # FK link to message created through other event in this loop
                continue

            try:
                sm = StoredMessage.objects.get(
                    # Careful: Mailgun annoyingly uses different formats for message id:
                    # message-id: [id] in Event, Message-Id: <[id]> in Message
                    data__contains={
                        'Message-Id': '<%s>' % orphan.data['message']['headers']['message-id']})
                # Message found, simply add pk
                orphan.stored_message = sm
                orphan.save()

            except StoredMessage.DoesNotExist:
                # Need to get and create the message
                try:
                    storage_url = orphan.data['storage']['url']
                except KeyError:
                    continue
                response = requests.get(
                    storage_url,
                    auth=("api", settings.MAILGUN_API_KEY)
                )
                if not response.status_code == 200:
                    continue
                response = response.json()
                sm = StoredMessage.objects.create(
                    data=response,
                    datetimestamp=parsedate_to_datetime(response['Date']))

                # Now deal with attachments
                for att_item in response['attachments']:
                    with TemporaryFile() as tf:
                        r = requests.get(att_item['url'],
                                         auth=("api", settings.MAILGUN_API_KEY),
                                         stream=True)
                        for chunk in r.iter_content(chunk_size=8192):
                            tf.write(chunk)
                        tf.seek(0)
                        af = AttachmentFile.objects.create(data=att_item)
                        af.file.save(att_item['name'], File(tf))
                        sm.attachment_files.add(af)

                # Finally add a FK relation to any event associated to this new message
                msgid = (sm.data['Message-Id'].lstrip('<')).rstrip('>')
                Event.objects.filter(
                    data__message__headers__contains={'message-id': msgid}
                ).update(stored_message=sm)
