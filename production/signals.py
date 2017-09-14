from notifications.signals import notify


def notify_new_stream(sender, instance, recipient, **kwargs):
    """
    Notify the production team about a new Production Stream created.
    """
    notify.send(sender=sender, recipient=recipient, actor=sender,
                verb=' assigned you to a Production Stream.', target=instance)


def notify_new_event(sender, instance, created, **kwargs):
    """
    Notify the production team about a new Production Event created.
    """
    if created:
        for officer in instance.stream.officers.all():
            notify.send(sender=sender, recipient=officer.user, actor=instance.noted_by.user,
                        verb=' created a new Production Event.', target=instance)


def notify_stream_completed(sender, instance, **kwargs):
    """
    Notify the production team about a Production Stream being completed.
    """
    for officer in instance.officers.all():
        notify.send(sender=sender, recipient=officer.user, actor=sender,
                    verb=' marked Production Stream as completed.', target=instance)
