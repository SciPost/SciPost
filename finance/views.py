from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from production.forms import ProductionUserMonthlyActiveFilter


@permission_required('scipost.can_view_timesheets', raise_exception=True)
def timesheets(request):
    """
    See an overview per month of all timesheets.
    """
    form = ProductionUserMonthlyActiveFilter(request.GET or None)
    context = {
        'form': form,
    }

    # if form.is_valid():
    context['totals'] = form.get_totals()

    return render(request, 'finance/timesheets.html', context)
