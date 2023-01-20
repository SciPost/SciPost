__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import get_object_or_404, render

from colleges.permissions import fellowship_required
from submissions.models import Submission


@fellowship_required()
def _hx_submission_fellow_appraisal(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = { "submission": submission}
    return render(
        request,
        "submissions/pool/_hx_submission_fellow_appraisal.html",
        context,
    )
