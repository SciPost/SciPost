__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.shortcuts import render


from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.mixins import PermissionRequiredMixin

from scipost.mixins import PermissionsMixin

from .models import Queue
from .forms import QueueForm


class HelpdeskView(ListView):
    model = Queue
    template_name = 'helpdesk/helpdesk.html'


class QueueCreateView(PermissionsMixin, CreateView):
    """
    Add a new Queue. Accessible to users with permission: can_add_queue.
    """
    permission_required = 'helpdesk.add_queue'
    model = Queue
    form_class= QueueForm
    template_name = 'helpdesk/queue_form.html'


class QueueUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'helpdesk.update_queue'
    model = Queue
    form_class= QueueForm
    template_name = 'helpdesk/queue_form.html'


class QueueDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'helpdesk.can_view_queue'
    model = Queue
    template_name = 'helpdesk/queue_detail.html'
