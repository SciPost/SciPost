__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from forums.models import Post


class Command(BaseCommand):
    help = "For all Post instances, this updates the calculated fields."

    def handle(self, *args, **kwargs):
        for post in Post.objects.all():
            post.update_cfs()
        self.stdout.write(
            self.style.SUCCESS("Successfully updated Post calculated fields")
        )
