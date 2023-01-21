__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from ethics.models import SubmissionClearance, CompetingInterest
from ethics.forms import SubmissionCompetingInterestForm

from colleges.permissions import is_edadmin
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
    return render(
        request,
        "submissions/pool/_hx_appraisal.html",
        context={"submission": submission},
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
    return render(
        request,
        "submissions/pool/_hx_appraisal.html",
        context={"submission": submission},
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
        submission.fellows.remove(request.user.contributor.session_fellowship(request))
        return redirect(reverse("submissions:pool:pool"))
        response = render(
            request,
            "submissions/pool/_hx_appraisal.html",
            context={"submission": submission},
        )
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


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_competing_interest_delete(request, identifier_w_vn_nr, pk):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    competing_interest = get_object_or_404(CompetingInterest, pk=pk)
    competing_interest.affected_submissions.remove(submission)
    submission.fellows.add(request.user.contributor.session_fellowship(request))
    if (competing_interest.affected_submissions.count() == 0 and
        competing_interest.affected_publications.count() == 0):
        competing_interest.delete()
    context = {"submission": submission, }
    return render(
        request,
        "ethics/_submission_competing_interests_details.html",
        context,
    )
