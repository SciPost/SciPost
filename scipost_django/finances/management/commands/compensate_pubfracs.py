__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from finances.models import Subsidy


class Command(BaseCommand):
    help = "Applies compensations from Subsidies to PubFracs"

    def handle(self, *args, **kwargs):
        nr_updated = Subsidy.compensate_pubfracs()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully compensated {nr_updated} PubFracs.")
        )
