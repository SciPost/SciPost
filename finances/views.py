from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.views.generic.edit import DeleteView

from .forms import LogsMonthlyActiveFilter
from .models import WorkLog
from .utils import slug_to_id


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
