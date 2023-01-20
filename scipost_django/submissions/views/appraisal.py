__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from colleges.permissions import fellowship_required
from submissions.models import Submission, Qualification
from submissions.forms import QualificationForm


@fellowship_required()
def _hx_appraisal(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    context = { "submission": submission}
    fellowship = request.user.contributor.session_fellowship(request)
    return render(
        request,
        "submissions/pool/_hx_appraisal.html",
        context,
    )


@fellowship_required()
def _hx_qualification_form(request, identifier_w_vn_nr=None):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    fellow = request.user.contributor.session_fellowship(request)
    try:
        instance = Qualification.objects.get(submission=submission, fellow=fellow)
    except Qualification.DoesNotExist:
        instance = None
    if request.method == "POST":
        form = QualificationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            response = render(
                request,
                "submissions/pool/_hx_appraisal.html",
                context={"submission": submission},
            )
            response["HX-Retarget"] = f"#submission-{submission.id}-appraisal"
            return response
    else:
        if instance:
            form = QualificationForm(instance=instance)
        else:
            form = QualificationForm(
                initial={"submission": submission, "fellow": fellow},
            )
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "submissions/pool/_hx_qualification_form.html",
        context,
    )