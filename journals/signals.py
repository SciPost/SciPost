__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import User, Group

from notifications.signals import notify


def notify_manuscript_published(sender, instance, created, **kwargs):
    """
    Notify the authors about their new Publication.

    instance -- Publication instance
    """
    if instance.is_published:
        editorial_administration = Group.objects.get(name='Editorial Administrators')
        for profile in instance.authors.all():
            if profile.has_active_contributor:
                notify.send(sender=sender, recipient=profile.contributor.user,
                            actor=editorial_administration,
                            verb=' published your manuscript.', target=instance)
