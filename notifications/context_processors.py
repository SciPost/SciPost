def get_notifications(request):
    return getattr(request, 'notifications', [])


def get_unread_count(request):
    return getattr(request, 'notifications_unread', 0)


def notifications(request):
    """ Return a lazy 'notifications' context variable. """
    return {
        'notifications': get_notifications(request),
        'notifications_unread': get_unread_count(request)
    }
