__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.core.management import BaseCommand

from ...models import ComposedMessage, ComposedMessageAPIResponse


class Command(BaseCommand):

    def handle(self, *args, **options):
        emails_ready_to_send = ComposedMessage.objects.ready()

        for msg in emails_ready_to_send:
            data = {
                'from': msg.from_account.email,
                'to': msg.to_recipient,
                'subject': msg.subject,
                'text': msg.body_text,
                'html': msg.body_html,
            }
            if msg.cc_recipients:
                data['cc'] = msg.cc_recipients
            if msg.bcc_recipients:
                data['bcc'] = msg.bcc_recipients

            # RFC 2822 MIME headers:
            for key, val in msg.headers_added.items():
                h_key = "h:%s" % key
                data[h_key] = val

            files = [('attachment', (att.data['name'], att.file.read()))
                     for att in msg.attachment_files.all()]

            response = requests.post(
                "https://api.eu.mailgun.net/v3/%s/messages" % msg.from_account.domain.name,
                auth=("api", settings.MAILGUN_API_KEY),
                files=files,
                data=data)

            msgr = ComposedMessageAPIResponse(
                message=msg,
                status_code=response.status_code,
                json=response.json())
            msgr.save()

            if response.status_code == 200:
                ComposedMessage.objects.filter(uuid=msg.uuid
                ).update(status=ComposedMessage.STATUS_SENT)
