__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from colleges import factories


class Command(BaseCommand):
    help = "Create random Fellowships objects using the factories."

    def add_arguments(self, parser):
        parser.add_argument(
            "number",
            action="store",
            default=0,
            type=int,
            help="Number of Fellowships to add",
        )

    def handle(self, *args, **kwargs):
        self.create_fellowships(kwargs["number"])

    def create_fellowships(self, n):
        factories.FellowshipFactory.create_batch(n)
        self.stdout.write(
            self.style.SUCCESS("Successfully created {n} Fellowships.".format(n=n))
        )
