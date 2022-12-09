__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import operator

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from guardian.shortcuts import get_objects_for_user

from colleges.permissions import is_edadmin
from submissions.models import Submission


@login_required
@user_passes_test(is_edadmin)
def edadmin(request):
    """
    Editorial administration page.
    """
    context = { "stages": Submission.STAGE_SLUGS }
    return render(request, "edadmin/edadmin.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_submissions_in_stage(request, stage):
    """
    List Submissions in a given stage.
    """
    if stage not in Submission.STAGE_SLUGS:
        raise Http404(f"This Submission stage does not exist: {stage}")
    submissions = get_objects_for_user(request.user, "submissions.take_edadmin_actions")
    submissions = operator.attrgetter(f"in_stage_{stage}")(submissions)()
    paginator = Paginator(submissions, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "stage": stage,
        "count": count,
        "page_obj":
        page_obj,
        "start_index": start_index,
    }
    return render(request, "edadmin/_hx_submissions_list.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_submission(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {"submission": submission,}
    return render(request, "edadmin/_hx_submission.html", context)
