__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import csv
from datetime import datetime

from django.core.management.base import BaseCommand

from colleges.models import Fellowship


class Command(BaseCommand):
    """
    Use this command to export the (currently active, non-guest) Fellows table.
    """

    def handle(self, *args, **kwargs):
        # File variables
        filename = "export_%s_active_Fellows.csv" % datetime.now().strftime("%Y_%m_%d")
        filename = filename.replace(" ", "_")

        # Query
        queryset = Fellowship.objects.active().filter(guest=False)

        # Open + write the file
        with open(filename, "w") as _file:
            for f in queryset.all():
                aff = f.contributor.profile.affiliations.first()
                aff_text = ""
                if aff:
                    aff_text = (
                        str(aff.organization) + ", " + aff.organization.country.name
                    )
                print(f, ",", f.contributor.profile.email, ",", aff_text, file=_file)
