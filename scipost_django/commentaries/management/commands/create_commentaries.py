__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from commentaries import factories


class Command(BaseCommand):
    help = "Create random Commentaries objects using the factories."

    def add_arguments(self, parser):
        parser.add_argument(
            "number",
            action="store",
            default=0,
            type=int,
            help="Number of Commentaries to add",
        )

    def handle(self, *args, **kwargs):
        self.create_commentaries(kwargs["number"])

    def create_commentaries(self, n):
        factories.CommentaryFactory.create_batch(n)
        self.stdout.write(
            self.style.SUCCESS("Successfully created {n} Commentaries.".format(n=n))
        )
