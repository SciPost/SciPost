__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from organizations.models import Organization


class Command(BaseCommand):
    help = (
        "For all Organization model instances, "
        "this updates the calculated field cf_associated_publication_ids"
    )

    def handle(self, *args, **kwargs):
        for org in Organization.objects.all():
            org.update_cf_associated_publication_ids()
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully updated Organization:cf_associated_publication_ids."
            )
        )
