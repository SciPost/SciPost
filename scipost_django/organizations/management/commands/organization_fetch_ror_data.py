__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from organizations.models import Organization
from organizations.utils import RORAPIHandler


class Command(BaseCommand):
    help = (
        "For all Organization model instances, "
        "this command updates the `ror_json` field by fetching the latest data "
        "using the `id` property of the `ror_json` field."
    )

    def handle(self, *args, **kwargs):
        ror_api_handler = RORAPIHandler()

        updated = 0
        missing = 0
        for org in Organization.objects.all():
            if ror_id := org.ror_json.get("id", None):
                org.ror_json = ror_api_handler.from_id(ror_id)
                org.save()
                updated += 1
            else:
                missing += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated} organizations, {missing} organizations missing `id`"
            )
        )
