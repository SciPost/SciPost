from django.contrib.auth.models import Group, User

from notifications.signals import notify


def notify_new_stream(sender, instance, created, **kwargs):
    """
    Notify the production team about a new Production Stream created.
    """
    if created:
        production_officers = User.objects.filter(groups__name='Production Officers')
        editorial_college = Group.objects.get(name='Editorial College')
        for user in production_officers:
            notify.send(sender=sender, recipient=user, actor=editorial_college, verb=' accepted a submission. A new productionstream has been started.', target=instance)


def notify_new_event(sender, instance, created, **kwargs):
    """
    Notify the production team about a new Production Event created.
    """
    if created:
        production_officers = User.objects.filter(groups__name='Production Officers')
        for user in production_officers:
            notify.send(sender=sender, recipient=user, actor=instance.noted_by.user, verb=' created a new Production Event ', target=instance)


def notify_stream_completed(sender, instance, **kwargs):
    """
    Notify the production team about a Production Stream being completed.
    """
    production_officers = User.objects.filter(groups__name='Production Officers')
    for user in production_officers:
        notify.send(sender=sender, recipient=user, actor=sender, verb=' marked Production Stream as completed.', target=instance)
