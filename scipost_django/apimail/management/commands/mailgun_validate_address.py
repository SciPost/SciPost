__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.core.management import BaseCommand


def validate_address(address=None):
    if address:
        response = requests.get(
             "https://api.mailgun.net/v4/address/validate",
            auth=("api", settings.MAILGUN_API_KEY),
            params={"address": address}
        ).json()
        return response


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--address', type=str, required=False,
            help='email address to validate')

    def handle(self, *args, **options):
        result = validate_address(options.get('address'))
        print(result)
