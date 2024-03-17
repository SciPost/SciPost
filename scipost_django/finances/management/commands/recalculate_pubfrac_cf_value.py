__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from finances.models import PubFrac


class Command(BaseCommand):
    help = "For all PubFrac objects, recompute the cf_value field"

    def handle(self, *args, **kwargs):
        for pf in PubFrac.objects.all():
            pf.cf_value = 0 # just trigger recomputation via the save method
            pf.save()
