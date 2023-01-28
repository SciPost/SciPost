__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render

from edadmin.forms.monitor import EdAdminFellowshipSearchForm


from colleges.models import College, Fellowship
from colleges.permissions import is_edadmin_or_senior_fellow


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def fellow_activity(request):
    """
    Monitor activity of Fellows for the Colleges to which this user belongs.
    """
    if request.user.contributor.is_ed_admin:
        colleges = College.objects.all()
    else:
        colleges = College.objects.filter(pk__in=[
            f.college.id for f in request.user.contributor.fellowships.all()
        ])
    context = {
        "colleges": colleges,
    }
    return render(
        request,
        "edadmin/monitor/fellow_activity.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_college_fellow_activity_table(request, college):
    form = EdAdminFellowshipSearchForm(request.POST or None, college=college)
    form.is_valid()
    fellowships = form.search_results() # use it always
    context = {
        "college": college,
        "fellowships": fellowships,
        "form": form,
    }
    return render(
        request,
        "edadmin/monitor/_hx_college_fellow_activity_table.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_fellow_stage_assignment_appraisals_table(request, fellowship_id: int):
    """
    Provide a table of this Fellow's appraisals for Submissions in Assignment stage.
    """
    fellowship = get_object_or_404(Fellowship, pk=fellowship_id)
    context = {"fellowship": fellowship,}
    return render(
        request,
        "edadmin/monitor/_hx_fellow_stage_assignment_appraisals_table.html",
        context,
    )
