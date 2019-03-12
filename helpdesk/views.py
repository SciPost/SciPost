__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import get_groups_with_perms, get_objects_for_user, remove_perm
from scipost.mixins import PermissionsMixin

from .models import Queue
from .forms import QueueForm


class HelpdeskView(ListView):
    model = Queue
    template_name = 'helpdesk/helpdesk.html'

    def get_queryset(self):
        return get_objects_for_user(self.request.user, 'helpdesk.can_view_queue').anchors()


class QueueCreateView(PermissionsMixin, CreateView):
    """
    Add a new Queue. Accessible to users with permission: can_add_queue.
    """
    permission_required = 'helpdesk.add_queue'
    model = Queue
    form_class= QueueForm
    template_name = 'helpdesk/queue_form.html'

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        try:
            parent_slug = self.kwargs.get('parent_slug')
            parent_queue = get_object_or_404(Queue, slug=parent_slug)
            initial.update({
                'managing_group': parent_queue.managing_group,
                'response_groups': parent_queue.response_groups.all(),
                'parent_queue': parent_queue,
            })
        except KeyError:
            pass
        return initial


class QueueUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'helpdesk.update_queue'
    model = Queue
    form_class= QueueForm
    template_name = 'helpdesk/queue_form.html'


class QueueDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'helpdesk.delete_queue'
    model = Queue
    success_url = reverse_lazy('helpdesk:helpdesk')

    def delete(self, request, *args, **kwargs):
        """
        A Queue can only be deleted if it has no descendant Queues.
        Upon deletion, all object-level permissions associated to the
        Queue are explicitly removed, to avoid orphaned permissions.
        """
        queue = get_object_or_404(Queue, slug=self.kwargs.get('slug'))
        groups_perms_dict = get_groups_with_perms(queue, attach_perms=True)
        if queue.sub_queues.all().count() > 0:
            messages.warning(request, 'A Queue with sub-queues cannot be deleted.')
            return redirect(queue.get_absolute_url())
        for group, perms_list in groups_perms_dict.items():
            for perm in perms_list:
                remove_perm(perm, group, queue)
        return super().delete(request, *args, **kwargs)


class QueueDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'helpdesk.can_view_queue'
    model = Queue
    template_name = 'helpdesk/queue_detail.html'
