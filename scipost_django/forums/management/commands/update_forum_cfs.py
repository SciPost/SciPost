__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from forums.models import Forum


class Command(BaseCommand):
    help = "For all Forum instances, this updates the calculated fields."

    def handle(self, *args, **kwargs):
        for forum in Forum.objects.all():
            forum.update_cfs()
        self.stdout.write(
            self.style.SUCCESS("Successfully updated Forum calculated fields")
        )
