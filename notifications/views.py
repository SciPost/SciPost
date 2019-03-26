__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
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
    # if not request.user.is_authenticated():
    #     data = {
    #         'unread_count': 0,
    #         'list': []
    #     }
    #     return JsonResponse(data)

    data = {
        'unread_count': 0,
        'list': []
    }
    return JsonResponse(data)
