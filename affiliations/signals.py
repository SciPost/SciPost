__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import User

from notifications.models import FakeActors
from notifications.signals import notify


def notify_new_affiliation(sender, instance, created, **kwargs):
    """Notify the SciPost Administration about a new Affiliation created to check it."""
    if created:
        administrators = User.objects.filter(groups__name='SciPost Administrators')
        actor, __ = FakeActors.objects.get_or_create(name='A SciPost user')
        for user in administrators:
            notify.send(sender=sender, recipient=user, actor=actor,
                        verb=' created a new Institution instance. You may want to validate it.',
                        target=instance)
