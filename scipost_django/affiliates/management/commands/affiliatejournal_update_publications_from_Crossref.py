__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from affiliates.models import AffiliateJournal
from affiliates.services import get_affiliatejournal_publications_from_Crossref


class Command(BaseCommand):
    help = (
        "For all AffiliateJournal model instances, "
        "fetch recent publications from Crossref."
    )

    def handle(self, *args, **kwargs):
        for journal in AffiliateJournal.objects.all():
            get_affiliatejournal_publications_from_Crossref(journal)
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully updated AffiliateJournal publications."
            )
        )
