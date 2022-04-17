__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from ...constants import NORMAL_CONTRIBUTOR
from ...models import Contributor
from profiles.models import Profile


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
        profile, created = Profile.objects.get_or_create(
            title='MX',
            first_name=user.first_name,
            last_name=user.last_name,
        )
        contributor, created = Contributor.objects.get_or_create(
            profile=profile,
            user=user,
            status=NORMAL_CONTRIBUTOR,
        )
        contributor.save()
        Contributor.objects.filter(pk=contributor.id).update(vetted_by=contributor)
        contributor.user.groups.add(Group.objects.get(name="Registered Contributors"))


    def handle(self, *args, **options):
        self.create_contributor(options["username"])
