__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import requests

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand
from django.utils import timezone

from ...models import StoredMessage


class Command(BaseCommand):
    """
    For a StoredMessage, fetch the mime version from Mailgun API.
    """

    help = 'Gets a StoredMessage\'s mime version from the Mailgun API and saves it to file.'

    def handle(self, *args, **kwargs):
        tmin = timezone.now() - datetime.timedelta(
            days=settings.MAILGUN_STORED_MESSAGES_RETENTION_DAYS)
        sm_wo_mime = StoredMessage.objects.filter(
            datetimestamp__gt=tmin,
            mime__in=['', None])
        nr_fetched = 0
        for sm in sm_wo_mime.all():
            try: # get storage url from the associated events
                storage_url = sm.event_set.first().data['storage']['url']
            except KeyError:
                continue
            r = requests.get(
                storage_url,
                auth=("api", settings.MAILGUN_API_KEY),
                headers={'Accept': 'message/rfc2822'}
            )
            if not r.status_code == 200:
                continue
            r_json = r.json()
            sm.mime.save("%s.mime" % str(sm.uuid), ContentFile(r_json['body-mime']))
            nr_fetched += 1
        print("Fetched %d message MIME instances." % nr_fetched)
