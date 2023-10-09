__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.core.management import BaseCommand

from ...exceptions import APIMailError
from ...models import Domain


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--from", type=str, required=True, help="from address")
        parser.add_argument("--to", type=str, required=True, help="to address")

    def handle(self, *args, **options):
        domain_name = options.get("from").rpartition("@")[2]
        try:
            Domain.objects.active().get(name=domain_name)
            data = {
                "from": options.get("from"),
                "to": options.get("to"),
                "subject": "Test outgoing email",
                "text": "Testing outgoing email.",
            }
            response = requests.post(
                "https://api.eu.mailgun.net/v3/%s/messages" % domain_name,
                auth=("api", settings.MAILGUN_API_KEY),
                data=data,
            )

        except Domain.MultipleObjectsReturned:
            raise APIMailError("Multiple domains found in mailgun_send_test_email")
        except Domain.DoesNotExist:
            raise APIMailError(
                "The sending domain was not recognized in mailgun_send_test_email"
            )
