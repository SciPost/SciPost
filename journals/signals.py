from django.contrib.auth.models import User, Group

from notifications.signals import notify


def notify_manuscript_published(sender, instance, created, **kwargs):
    """
    Notify the authors about their new Publication.

    instance -- Publication instance
    """
    if instance.is_published:
        authors = User.objects.filter(contributor__publications=instance)
        editorial_administration = Group.objects.get(name='Editorial Administrators')
        for user in authors:
            notify.send(sender=sender, recipient=user, actor=editorial_administration,
                        verb=' published your manuscript.', target=instance)
