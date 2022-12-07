__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import operator

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.shortcuts import render

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
    context = {
        "submissions": operator.attrgetter(f"in_stage_{stage}")(submissions)(),
    }
    return render(request, "edadmin/_hx_submissions_list.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_edadmin(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {"submission": submission,}
    return render(request, "edadmin/_hx_submission_edadmin.html", context)
