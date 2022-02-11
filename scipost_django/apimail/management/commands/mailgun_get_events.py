__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import time
import requests

from django.conf import settings
from django.core.management import BaseCommand

from ...exceptions import APIMailError
from ...models import Domain, Event


def get_and_save_events(url=None, domain_name=None, nr_minutes=2):
    """
    For the given domain, get events from Mailgun Events API.

    This method treats a single page and saves new Events to the database.
    If no url is given, get the first page.
    Returns the paging JSON, if present, so traversing can be performed.
    """
    response = {}
    if url is None and domain_name is None:
        raise APIMailError(
            "Please provide either a url or domain_name to get_and_save_events."
        )
    elif url:
        response = requests.get(url, auth=("api", settings.MAILGUN_API_KEY)).json()
    else:
        print("Fetching items for the last %d minutes" % nr_minutes)
        begin_time = int(time.time()) - 60 * nr_minutes
        response = requests.get(
            "https://api.eu.mailgun.net/v3/%s/events" % domain_name,
            auth=("api", settings.MAILGUN_API_KEY),
            params={"begin": begin_time, "ascending": "yes"},
        ).json()
        print(response)
    try:
        events = response["items"]
        print("Retrieved %d events" % len(response["items"]))
        for item in events:
            if not Event.objects.filter(
                data__timestamp=item["timestamp"], data__id=item["id"]
            ).exists():
                Event.objects.create(data=item)
        info = {"nitems": len(events)}
        if "paging" in response:
            info["paging"] = response["paging"]
        return info
    except KeyError:
        print("No items found for domain %s\nresponse: %s" % (domain_name, response))
    return {"nitems": 0}


class Command(BaseCommand):
    """
    Perform a GET request to harvest Events from the Mailgun API, saving them to the DB.
    """

    help = "Gets Events from the Mailgun Events API and saves them to the DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--nr_minutes",
            action="store",
            dest="nr_minutes",
            type=int,
            help="number of minutes in the past where events are to be retrieved",
        )

    def handle(self, *args, **kwargs):
        nr_minutes = kwargs.get("nr_minutes", 2)
        print("Getting events for the last %d minutes" % nr_minutes)
        for domain in Domain.objects.active():
            info = get_and_save_events(domain_name=domain.name, nr_minutes=nr_minutes)
            ctr = 1  # Safety: ensure no runaway requests
            while ctr < 100 and info["nitems"] > 0:
                info = get_and_save_events(url=info["paging"]["next"])
                ctr += 1
                if ctr == 100:
                    raise APIMailError(
                        "Hard stop of mailgun_get_events: "
                        "harvested above 100 pages from Mailgun Events API"
                    )
