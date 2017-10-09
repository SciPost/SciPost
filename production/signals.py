from django.contrib.auth.models import Group

from notifications.signals import notify


def notify_new_stream(sender, instance, created, **kwargs):
    """
    Notify the production supervisors about a new Production Stream that is created.
    """
    if created:
        editorial_college = Group.objects.get(name='Editorial College')
        supervisors = Group.objects.get(name='Production Supervisor')
        for recipient in supervisors.user_set.all():
            notify.send(sender=sender, recipient=recipient, actor=editorial_college,
                        verb=' accepted a Submission. A new Production Stream has started.',
                        target=instance)


def notify_new_stream_assignment(sender, instance, recipient, **kwargs):
    """
    Notify a production officer about its new Production Stream assignment.
    """
    notify.send(sender=sender, recipient=recipient, actor=sender,
                verb=' assigned you to a Production Stream.', target=instance)


def notify_new_event(sender, instance, created, **kwargs):
    """
    Notify the production team about a new Production Event created.
    """
    if created:
        stream = instance.stream

        if stream.officer and stream.officer != instance.noted_by:
            notify.send(sender=sender, recipient=stream.officer.user,
                        actor=instance.noted_by.user,
                        verb=' created a new Production Event.', target=instance)

        if stream.supervisor and stream.supervisor != instance.noted_by:
            notify.send(sender=sender, recipient=stream.supervisor.user,
                        actor=instance.noted_by.user,
                        verb=' created a new Production Event.', target=instance)


def notify_stream_completed(sender, instance, **kwargs):
    """
    Notify the production team about a Production Stream being completed.
    """
    notify.send(sender=sender, recipient=instance.officer.user,
                actor=sender, verb=' marked Production Stream as completed.', target=instance)

    notify.send(sender=sender, recipient=instance.supervisor.user,
                actor=sender, verb=' marked Production Stream as completed.', target=instance)
