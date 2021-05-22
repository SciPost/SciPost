__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import csv
from datetime import datetime

from django.core.management.base import BaseCommand

from ...constants import NORMAL_CONTRIBUTOR
from ...models import Contributor


class Command(BaseCommand):
    """
    Use this command to export the Contributor table. One could filter the export
    by simply using the --group argument.

    For example, one could run:
    $ ./manage.py export_contributors --group 'Registered Contributors'
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            dest='group',
            default=False,
            type=str,
            help='Filter the contributors by their group name'
        )

    def handle(self, *args, **kwargs):
        # File variables
        filename = 'export_%s_contributors_%s.csv' % (datetime.now().strftime('%Y_%m_%d_%H_%M'),
                                                      kwargs.get('group', ''))
        filename = filename.replace(' ', '_')
        fieldnames = ['first_name', 'last_name', 'email_address']

        # Query
        queryset = Contributor.objects.filter(user__is_active=True,
                                              status=CONTRIBUTOR_NORMAL,
                                              profile__accepts_SciPost_emails=True)
        if kwargs['group']:
            queryset = queryset.filter(user__groups__name=kwargs['group'])

        # Open + write the file
        with open(filename, 'w', newline='') as _file:
            writer = csv.writer(_file, quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(fieldnames)
            n = 0
            for contributor in queryset:
                user = contributor.user
                writer.writerow([user.first_name, user.last_name, user.email])
                n += 1
        self.stdout.write(self.style.SUCCESS('Successfully wrote %i Contributors to file %s.' % (
            n, filename
        )))
