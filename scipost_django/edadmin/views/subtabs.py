__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render

from colleges.permissions import is_edadmin
from submissions.models import Submission


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_edadmin_subtab(request, identifier_w_vn_nr, subtab):
    submission = get_object_or_404(
        Submission,
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = {
        "submission": submission,
        "subtab": subtab,
    }
    return render(request, "edadmin/_hx_submission_edadmin_subtab.html", context)
