__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from guardian.shortcuts import get_objects_for_user

from colleges.permissions import is_edadmin
from submissions.models import (
    Submission,
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
)
from submissions.forms import iThenticateReportForm

from edadmin.forms.plagiarism import (
    InternalPlagiarismAssessmentForm,
    iThenticatePlagiarismAssessmentForm,
)


@login_required
@user_passes_test(is_edadmin)
def _hx_incoming_list(request):
    """
    EdAdmin page for incoming Submissions.
    """
    submissions = get_objects_for_user(request.user, "submissions.take_edadmin_actions")
    context = {
        "phase": "incoming",
        "submissions": submissions.incoming(),
    }
    return render(request, "edadmin/_hx_submissions_list.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_details_contents(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {"submission": submission,}
    return render(request, "edadmin/_hx_submission_details_contents.html", context)


########################
# Plagiarism: internal #
########################

@login_required
@user_passes_test(is_edadmin)
def _hx_plagiarism_internal(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {
        "submission": submission,
        "submission_matches": [],
        "publication_matches": [],
    }
    if "submission_matches" in submission.internal_plagiarism_matches:
        for sub_match in submission.internal_plagiarism_matches["submission_matches"]:
            context["submission_matches"].append(
                {
                    "submission": Submission.objects.get(
                        preprint__identifier_w_vn_nr=sub_match["identifier_w_vn_nr"],
                    ),
                    "ratio_title": sub_match["ratio_title"],
                    "ratio_authors": sub_match["ratio_authors"],
                    "ratio_abstract": sub_match["ratio_abstract"],
                }
            )
    if "publication_matches" in submission.internal_plagiarism_matches:
        for pub_match in submission.internal_plagiarism_matches["publication_matches"]:
            context["publication_matches"].append(
                {
                    "publication": Publication.objects.get(doi_label=pub_match["doi_label"]),
                    "ratio_title": pub_match["ratio_title"],
                    "ratio_authors": pub_match["ratio_authors"],
                    "ratio_abstract": pub_match["ratio_abstract"],
                }
            )
    return render(request, "edadmin/_hx_plagiarism_internal.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_plagiarism_internal_assess(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    # if Submission has no assessment yet, create one:
    try:
        submission.internal_plagiarism_assessment
    except InternalPlagiarismAssessment.DoesNotExist:
        assessment = InternalPlagiarismAssessment(submission=submission)
        assessment.save()
        submission.refresh_from_db()
    form = InternalPlagiarismAssessmentForm(
        request.POST or None,
        instance=submission.internal_plagiarism_assessment,
    )
    if form.is_valid(): # just trigger re-rendering of iThenticate div
        assessment = form.save()
        response = HttpResponse()
        response["HX-Trigger"] = f"{submission.pk}-plagiarism-internal-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(request, "edadmin/_hx_plagiarism_internal_assess.html", context)


###########################
# Plagiarism: iThenticate #
###########################

@login_required
@user_passes_test(is_edadmin)
def _hx_plagiarism_iThenticate(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = iThenticateReportForm(submission, request.POST or None)
    if form.is_valid():
        form.save()
        submission.refresh_from_db()
    context = {
        "submission": submission,
        "form": form,
    }
    return render(request, "edadmin/_hx_plagiarism_iThenticate.html", context)


@login_required
@user_passes_test(is_edadmin)
def _hx_plagiarism_iThenticate_assess(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    # if Submission has no assessment yet, create one:
    try:
        submission.iThenticate_plagiarism_assessment
    except iThenticatePlagiarismAssessment.DoesNotExist:
        assessment = iThenticatePlagiarismAssessment(submission=submission)
        assessment.save()
        submission.refresh_from_db()
    form = iThenticatePlagiarismAssessmentForm(
        request.POST or None,
        instance=submission.iThenticate_plagiarism_assessment,
    )
    if form.is_valid(): # just trigger re-rendering of iThenticate div
        assessment = form.save()
        response = HttpResponse()
        response["HX-Trigger"] = f"{submission.pk}-plagiarism-iThenticate-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(request, "edadmin/_hx_plagiarism_iThenticate_assess.html", context)
