from django.contrib.auth.models import Group

from .import constants

from notifications.signals import notify


def notify_new_stream(sender, instance, created, **kwargs):
    """
    Notify the production supervisors about a new Production Stream that is created.
    """
    if created:
        editorial_college = Group.objects.get(name='Editorial College')
        administators = Group.objects.get(name='Editorial Administrators')
        for recipient in administators.user_set.all():
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


def notify_stream_status_change(sender, instance, created, **kwargs):
    """
    Notify the production officers about a new status change for a Production Stream.

    sender -- User instance
    instance -- ProductionStream instance
    """

    if instance.status == constants.PROOFS_ACCEPTED:
        administators = Group.objects.get(name='Editorial Administrators')
        for user in administators.user_set.all():
            notify.send(sender=sender, recipient=user,
                        actor=sender,
                        verb=' has marked Proofs accepted.', target=instance)
    elif instance.status == constants.PROOFS_PUBLISHED:
        if instance.supervisor:
            notify.send(sender=sender, recipient=instance.supervisor.user,
                        actor=sender,
                        verb=' published the manuscript of your Production Stream.',
                        target=instance)

    elif instance.status == constants.PRODUCTION_STREAM_COMPLETED:
        if instance.supervisor:
            notify.send(sender=sender, recipient=instance.supervisor.user,
                        actor=sender,
                        verb=' marked your Production Stream as completed.', target=instance)
        if instance.officer:
            notify.send(sender=sender, recipient=instance.officer.user,
                        actor=sender,
                        verb=' marked your Production Stream as completed.', target=instance)
    else:
        if instance.officer:
            notify.send(sender=sender, recipient=instance.officer.user,
                        actor=sender,
                        verb=' changed the Production Stream status.', target=instance)

        if instance.supervisor:
            notify.send(sender=sender, recipient=instance.supervisor.user,
                        actor=sender,
                        verb=' changed the Production Stream status.', target=instance)


def notify_proof_upload(sender, instance, created, **kwargs):
    if created and instance.stream.supervisor:
        notify.send(sender=sender, recipient=instance.stream.supervisor.user,
                    actor=instance.uploaded_by.user, verb=' uploaded new Proofs to Production Stream.',
                    target=instance)
