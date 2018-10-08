__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .forms import SubsidyForm, LogsMonthlyActiveFilter
from .models import Subsidy, WorkLog
from .utils import slug_to_id

from scipost.mixins import PermissionsMixin



#############
# Subsidies #
#############

class SubsidyCreateView(PermissionsMixin, CreateView):
    """
    Create a new Subsidy.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = Subsidy
    form_class = SubsidyForm
    template_name = 'finances/subsidy_form.html'
    success_url = reverse_lazy('finances:subsidies')


class SubsidyUpdateView(PermissionsMixin, UpdateView):
    """
    Update a Subsidy.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = Subsidy
    form_class = SubsidyForm
    template_name = 'finances/subsidy_form.html'
    success_url = reverse_lazy('finances:subsidies')


class SubsidyDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Subsidy.
    """
    permission_required = 'scipost.can_manage_subsidies'
    model = Subsidy
    success_url = reverse_lazy('finances:subsidies')


class SubsidyListView(ListView):
    model = Subsidy


class SubsidyDetailView(DetailView):
    model = Subsidy


############################
# Timesheets and Work Logs #
############################

@permission_required('scipost.can_view_timesheets', raise_exception=True)
def timesheets(request):
    """
    See an overview per month of all timesheets.
    """
    form = LogsMonthlyActiveFilter(request.GET or None)
    context = {
        'form': form,
    }

    # if form.is_valid():
    context['totals'] = form.get_totals()

    return render(request, 'finances/timesheets.html', context)


class LogDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkLog

    def get_object(self):
        try:
            return WorkLog.objects.get(user=self.request.user, id=slug_to_id(self.kwargs['slug']))
        except WorkLog.DoesNotExist:
            raise Http404

    def get_success_url(self):
        messages.success(self.request, 'Log deleted.')
        return self.object.content.get_absolute_url()
