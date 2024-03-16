__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals.models import Publication


class Command(BaseCommand):
    help = "Recalculates PubFracs for all publications"

    def handle(self, *args, **kwargs):
        for pub in Publication.objects.all():
            pub.recalculate_pubfracs()
