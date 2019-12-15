__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--to', type=str, required=True,
            help='to address')

    def handle(self, *args, **options):
        data = {
            'to': options.get('to'),
            'from': 'techsupport@%s' % settings.MAILGUN_DOMAIN_NAME,
            'subject': 'Test outgoing email',
            'text': 'Testing outgoing email.'
        }
        response = requests.post(
            "https://api.eu.mailgun.net/v3/%s/messages" % settings.MAILGUN_DOMAIN_NAME,
            auth=("api", settings.MAILGUN_API_KEY),
            data=data)
        print(data)
        print(response)
