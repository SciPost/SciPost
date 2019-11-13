__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.core.management import BaseCommand

from ...exceptions import APIMailError
from ...models import Event


def get_and_save_events(url=None):
    """
    Get events from Mailgun Events API.

    This method treats a single page and saves new Events to the database.
    If no url is given, get the first page.
    Returns the paging JSON, if present, so traversing can be performed.
    """
    response = requests.get(
        url if url else "https://api.eu.mailgun.net/v3/%s/events" % settings.MAILGUN_DOMAIN_NAME,
        auth=("api", settings.MAILGUN_API_KEY)
    ).json()
    events = response['items']
    for item in events:
        if not Event.objects.filter(data__timestamp=item['timestamp'],
                                    data__id=item['id']).exists():
            Event.objects.create(data=item)
    info = {'nitems': len(events)}
    if 'paging' in response:
        info['paging'] = response['paging']
    return info


class Command(BaseCommand):
    """
    Perform a GET request to harvest Events from the Mailgun API, saving them to the DB.
    """

    help = 'Gets Events from the Mailgun Events API and saves them to the DB.'

    def handle(self, *args, **kwargs):
        info = get_and_save_events()
        ctr = 1 # Safety: ensure no runaway requests
        while ctr < 100 and info['nitems'] > 0:
            info = get_and_save_events(url=info['paging']['next'])
            ctr += 1
            if ctr == 100:
                raise APIMailError('Hard stop of mailgun_get_events: '
                                   'harvested above 100 pages from Mailgun Events API')
