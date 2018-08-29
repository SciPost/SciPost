__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from .models import Notification
from .utils import id2slug, slug2id


def is_test_user(user):
    """Check if user is test user.

    To be removed after test-phase is over.
    """
    return True
    return user.groups.filter(name='Testers').exists()


@login_required
@user_passes_test(is_test_user)
def forward(request, slug):
    """Open the url of the target object of the notification and redirect.

    In addition, mark the notification as read.
    """
    notification = get_object_or_404(Notification, recipient=request.user, id=slug2id(slug))
    notification.mark_as_read()
    if hasattr(notification.target, 'get_notification_url'):
        return redirect(notification.target.get_notification_url(notification.url_code))
    return redirect(notification.target.get_absolute_url())


@login_required
@user_passes_test(is_test_user)
def mark_toggle(request, slug=None):
    """Toggle mark as read."""
    id = slug2id(slug)

    notification = get_object_or_404(Notification, recipient=request.user, id=id)
    notification.mark_toggle()

    _next = request.GET.get('next')
    if _next:
        return redirect(_next)

    if request.GET.get('json'):
        return JsonResponse({'unread': notification.unread})

    return redirect('notifications:all')


def live_unread_notification_count(request):
    """Return JSON of unread messages count."""
    if not request.user.is_authenticated():
        data = {'unread_count': 0}
    else:
        data = {'unread_count': request.user.notifications.unread().count()}
    return JsonResponse(data)


def live_notification_list(request):
    """Return JSON of unread count and content of messages."""
    if not request.user.is_authenticated():
        data = {
            'unread_count': 0,
            'list': []
        }
        return JsonResponse(data)

    try:
        # Default to 5 as a max number of notifications
        num_to_fetch = max(int(request.GET.get('max', 10)), 1)
        num_to_fetch = min(num_to_fetch, 100)
    except ValueError:
        num_to_fetch = 5

    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        offset = 0

    list = []

    for n in request.user.notifications.all()[offset:offset + num_to_fetch]:
        struct = model_to_dict(n)
        # struct['unread'] = struct['pseudo_unread']
        struct['slug'] = id2slug(n.id)
        if n.actor:
            if isinstance(n.actor, User):
                # Humanize if possible
                struct['actor'] = '{f} {l}'.format(f=n.actor.first_name, l=n.actor.last_name)
            else:
                struct['actor'] = str(n.actor)
        if n.target:
            if hasattr(n.target, 'notification_name'):
                struct['target'] = n.target.notification_name
            else:
                struct['target'] = str(n.target)
            struct['forward_link'] = n.get_absolute_url()
        if n.action_object:
            struct['action_object'] = str(n.action_object)
        struct['timesince'] = n.timesince()

        list.append(struct)

    if request.GET.get('mark_as_read'):
        # Mark all as read
        request.user.notifications.mark_all_as_read()

    data = {
        'unread_count': request.user.notifications.unread().count(),
        'list': list
    }
    return JsonResponse(data)
