__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    def handle(self, *args, **options):
        superusers = User.objects.filter(is_superuser=True)
        admin_group = Group.objects.get(name="SciPost Administrators")

        for superuser in superusers:
            superuser.groups.add(admin_group)
            superuser.save()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully vetted {len(superusers)} superusers.")
        )
