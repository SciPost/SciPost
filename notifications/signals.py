from django.dispatch import Signal

notify = Signal(providing_args=[
    'recipient', 'actor', 'verb', 'action_object', 'target', 'description',
    'timestamp', 'level'
])


# Basic working method to send a notification to a user using signals:
#   ---
#     from notifications.signals import notify
#     notify.send(user, recipient=user, verb='you reached level 10')
#   ---
