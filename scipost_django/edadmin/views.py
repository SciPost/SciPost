__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from guardian.shortcuts import get_objects_for_user

from scipost.permissions import is_edadmin


@login_required
@user_passes_test(is_edadmin)
def edadmin(request):
    """
    Editorial administration page.
    """
    submissions = get_objects_for_user(request.user, "submissions.take_edadmin_actions")
    context = { "prescreening": submissions.prescreening() }
    return render(request, "edadmin/edadmin.html", context)
