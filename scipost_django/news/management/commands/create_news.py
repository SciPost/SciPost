__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from news import factories


class Command(BaseCommand):
    help = "Create random News Item objects using the factories."

    def add_arguments(self, parser):
        parser.add_argument(
            "number",
            action="store",
            default=0,
            type=int,
            help="Number of News items to add",
        )

    def handle(self, *args, **kwargs):
        self.create_news_items(kwargs["number"])

    def create_news_items(self, n):
        factories.NewsItemFactory.create_batch(n)
        self.stdout.write(
            self.style.SUCCESS("Successfully created {n} News Items.".format(n=n))
        )
