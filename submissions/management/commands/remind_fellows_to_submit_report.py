__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand
# from django.contrib.auth.models import User

from ...models import RefereeInvitation
from ...signals import notify_invitation_approaching_deadline, notify_invitation_overdue


class Command(BaseCommand):
    def handle(self, *args, **options):
        for invitation in RefereeInvitation.objects.approaching_deadline():
            notify_invitation_approaching_deadline(RefereeInvitation, invitation, False)
        for invitation in RefereeInvitation.objects.overdue():
            notify_invitation_overdue(RefereeInvitation, invitation, False)
