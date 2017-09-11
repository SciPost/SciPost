from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from .models import Notification
from .utils import id2slug, slug2id


@method_decorator(login_required, name='dispatch')
class NotificationViewList(ListView):
    context_object_name = 'notifications'


class AllNotificationsList(NotificationViewList):
    """
    Index page for authenticated user
    """
    def get_queryset(self):
        return self.request.user.notifications.all()


class UnreadNotificationsList(NotificationViewList):
    def get_queryset(self):
        return self.request.user.notifications.unread()


@login_required
def mark_all_as_read(request):
    request.user.notifications.mark_all_as_read()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)
    return redirect('notifications:unread')


@login_required
def mark_as_read(request, slug=None):
    id = slug2id(slug)

    notification = get_object_or_404(Notification, recipient=request.user, id=id)
    notification.mark_as_read()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)

    return redirect('notifications:unread')


@login_required
def mark_as_unread(request, slug=None):
    id = slug2id(slug)

    notification = get_object_or_404(Notification, recipient=request.user, id=id)
    notification.mark_as_unread()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)

    return redirect('notifications:unread')


@login_required
def delete(request, slug=None):
    id = slug2id(slug)

    notification = get_object_or_404(Notification, recipient=request.user, id=id)
    notification.delete()

    _next = request.GET.get('next')

    if _next:
        return redirect(_next)

    return redirect('notifications:all')


def live_unread_notification_count(request):
    if not request.user.is_authenticated():
        data = {'unread_count': 0}
    else:
        data = {'unread_count': request.user.notifications.unread().count()}
    return JsonResponse(data)


def live_unread_notification_list(request):
    if not request.user.is_authenticated():
        data = {
           'unread_count': 0,
           'unread_list': []
        }
        return JsonResponse(data)

    try:
        # Default to 5 as a max number of notifications
        num_to_fetch = max(int(request.GET.get('max', 5)))
        num_to_fetch = min(num_to_fetch, 100)
    except ValueError:
        num_to_fetch = 5

    unread_list = []

    for n in request.user.notifications.unread()[:num_to_fetch]:
        struct = model_to_dict(n)
        struct['slug'] = id2slug(n.id)
        if n.actor:
            struct['actor'] = str(n.actor)
        if n.target:
            struct['target'] = str(n.target)
        if n.action_object:
            struct['action_object'] = str(n.action_object)
        if n.data:
            struct['data'] = n.data
        unread_list.append(struct)
        if request.GET.get('mark_as_read'):
            n.mark_as_read()
    data = {
        'unread_count': request.user.notifications.unread().count(),
        'unread_list': unread_list
    }
    return JsonResponse(data)
