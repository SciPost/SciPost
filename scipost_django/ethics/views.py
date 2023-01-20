__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from ethics.models import SubmissionClearance, CompetingInterest
from ethics.forms import SubmissionCompetingInterestForm

from submissions.models import Submission


@login_required
def _hx_submission_ethics(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    clearance = SubmissionClearance.objects.filter(
            profile=request.user.contributor.profile,
            submission=submission,
    ).first()
    competing_interest = CompetingInterest.objects.filter(
        profile=request.user.contributor.profile,
        affected_submissions=submission,
    ).first()
    context = {
        "submission": submission,
        "clearance": clearance,
        "competing_interest": competing_interest,
    }
    return render(request, "ethics/_hx_submission_ethics.html", context)


@login_required
def _hx_submission_clearance_assert(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    clearance, created = SubmissionClearance.objects.get_or_create(
        profile=request.user.contributor.profile,
        submission=submission,
        asserted_by=request.user.contributor,
    )
    return redirect(
        reverse(
            "ethics:_hx_submission_ethics",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr,},
        )
    )


@login_required
def _hx_submission_clearance_revoke(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    SubmissionClearance.objects.filter(
        profile=request.user.contributor.profile,
        submission=submission,
        asserted_by=request.user.contributor, # can only revoke own clearances
    ).delete()
    return redirect(
        reverse(
            "ethics:_hx_submission_ethics",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr,},
        )
    )


#######################
# Competing interests #
#######################

@login_required
def _hx_submission_competing_interest_form(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    form = SubmissionCompetingInterestForm(
        request.POST or None,
        submission=submission,
        initial={
            "profile": request.user.contributor.profile,
            "declared_by": request.user.contributor,
        }
    )
    if form.is_valid():
        instance = form.save()
        instance.affected_submissions.add(submission)
        response = render(
            request,
            "submissions/pool/_hx_appraisal.html",
            context={"submission": submission},
        )
        response["HX-Retarget"] = f"#submission-{submission.id}-appraisal"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "ethics/_hx_submission_competing_interest_form.html",
        context,
    )
