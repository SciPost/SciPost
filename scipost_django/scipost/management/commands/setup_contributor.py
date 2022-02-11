__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from ...constants import NORMAL_CONTRIBUTOR
from ...models import Contributor


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            required=True,
            help="Username of user to use for contributor model",
        )

    def create_contributor(self, username):
        user = User.objects.get(username=username)
        contributor = Contributor(user=user, status=NORMAL_CONTRIBUTOR, title="MR")
        contributor.vetted_by = contributor
        contributor.save()

    def handle(self, *args, **options):
        self.create_contributor(options["username"])
