__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals.models import Publication
from journals.services import update_citedby


class Command(BaseCommand):
    help = "Updates all Cited-by data for all Publications"

    def handle(self, *args, **kwargs):
        publications = Publication.objects.published()

        for publication in publications:
            update_citedby(publication.doi_label)
