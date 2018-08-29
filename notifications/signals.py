__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.dispatch import receiver, Signal

from .models import Notification


notify = Signal(providing_args=[
    'recipient', 'actor', 'verb', 'action_object', 'target',
    'description', 'level', 'type', 'url_code'])


@receiver(notify)
def notify_receiver(sender, **kwargs):
    """Create a new Notification."""
    if not type(kwargs['recipient']) == list:
        recipient = [kwargs['recipient']]
    else:
        recipient = kwargs['recipient']

    for user in recipient:
        notification = Notification(
            recipient=user,
            actor=kwargs['actor'],
            verb=kwargs['verb'],
            action_object=kwargs.get('action_object'),
            target=kwargs.get('target'),
            description=kwargs.get('description'),
            level=kwargs.get('level', 'info'),
            internal_type=kwargs.get('type', ''),
            url_code=kwargs.get('url_code', '')
        )
        notification.save()
    return


# Basic working method to send a notification to a user using signals:
#   ---
#     from notifications.signals import notify
#     notify.send(user, recipient=user, verb='you reached level 10')
#   ---
