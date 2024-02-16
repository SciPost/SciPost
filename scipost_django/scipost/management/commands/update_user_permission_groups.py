__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Update the user's permission groups based on their roles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            required=False,
            help="The username of the user to update the permission groups for.",
        )

    def handle(self, *args, **kwargs):
        if kwargs["user"]:
            user = User.objects.get(username=kwargs["user"])
            self.update_groups_for_user(user)
        else:
            self.update_groups()

    def update_groups(self):
        users = User.objects.exclude(contributor__isnull=True)
        for user in users:
            self.update_groups_for_user(user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated the permission groups for {users.count()} users."
            )
        )

    def update_unless_admin(self, user: "User", groups: list["Group"], add: bool):
        """Adds the group to the user if add is True, otherwise removes it, unless the user is an admin."""
        is_admin = (
            user.is_superuser
            or user.is_staff
            or user.contributor.is_scipost_admin
            or user.contributor.is_ed_admin
        )

        if is_admin:
            return

        if add:
            user.groups.add(*groups)
        else:
            user.groups.remove(*groups)

        user.save()

    def update_groups_for_user(self, user: "User"):
        # Get the groups
        editorial_college = Group.objects.get(name="Editorial College")
        senior_fellow = Group.objects.get(name="Senior Fellow")

        # Get the user's roles from object associations
        is_fellow = user.contributor.is_active_fellow
        is_senior_fellow = user.contributor.is_active_senior_fellow

        ########### Update the groups ##########
        # fmt: off

        # Update editorial college groups
        self.update_unless_admin(user, [editorial_college], (is_fellow or is_senior_fellow))
        self.update_unless_admin(user, [senior_fellow], is_senior_fellow)

        # fmt: on
        ########################################
