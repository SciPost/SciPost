__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from finances.models import Subsidy


class Command(BaseCommand):
    help = "Applies compensations from Subsidies to PubFracs"

    def handle(self, *args, **kwargs):
        # All Subsidy-givers first compensate themselves, starting from oldest Subsidy
        for subsidy in Subsidy.objects.obtained().order_by("date_from"):
            subsidy.compensate_own_pubfracs()
        # then their children, again starting from oldest Subsidy
        for subsidy in Subsidy.objects.obtained().order_by("date_from"):
            subsidy.compensate_children_pubfracs()
