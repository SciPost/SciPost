__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from guardian.shortcuts import get_objects_for_user

from colleges.permissions import is_edadmin
from mails.utils import DirectMailUtil
from submissions.models import (
    Submission,
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
)
from submissions.forms import iThenticateReportForm

from edadmin.forms import (
    InternalPlagiarismAssessmentForm,
    iThenticatePlagiarismAssessmentForm,
    SubmissionAdmissibilityForm,
    SubmissionAdmissionForm,
)


#################
# Admissibility #
#################

@login_required
@user_passes_test(is_edadmin)
def _hx_submission_admissibility(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = SubmissionAdmissibilityForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data["admissibility"] == "pass":
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.ADMISSIBLE
            )
        else: # inadmissible, inform authors and set status to ADMISSION_FAILED
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.ADMISSION_FAILED
            )
            # send authors admission failed email
            mail_util = DirectMailUtil(
                "authors/admission_failed",
                submission=submission,
                comments_for_authors=form.cleaned_data["comments_for_authors"],
            )
            mail_util.send_mail()
        submission.refresh_from_db()
        # trigger re-rendering of the details-contents div
        response = HttpResponse()
        response["HX-Trigger"] = f"submission-{submission.pk}-tab-edadmin-updated"
        return response
    context = {"submission": submission, "form": form,}
    return render(
        request,
        "edadmin/incoming/_hx_submission_admissibility_form.html",
        context,
    )



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
    return render(request, "edadmin/incoming/_hx_plagiarism_internal.html", context)


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
    if form.is_valid(): # trigger re-rendering of details-contents div
        assessment = form.save()
        response = HttpResponse()
        response["HX-Trigger"] = f"submission-{submission.pk}-tab-edadmin-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "edadmin/incoming/_hx_plagiarism_internal_assess.html",
        context,
    )


###########################
# Plagiarism: iThenticate #
###########################

@login_required
@user_passes_test(is_edadmin)
def _hx_plagiarism_iThenticate(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = iThenticateReportForm(
        submission,
        request.POST or None,
        instance=submission.iThenticate_plagiarism_report,
    )
    if form.is_valid():
        form.save()
        submission.refresh_from_db()
    context = {
        "submission": submission,
        "form": form,
    }
    return render(request, "edadmin/incoming/_hx_plagiarism_iThenticate.html", context)


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
    if form.is_valid(): # trigger re-rendering of details-contents div
        assessment = form.save()
        response = HttpResponse()
        response["HX-Trigger"] = f"submission-{submission.pk}-tab-edadmin-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "edadmin/incoming/_hx_plagiarism_iThenticate_assess.html",
        context,
    )


#############
# Admission #
#############

@login_required
@user_passes_test(is_edadmin)
def _hx_submission_admission(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = SubmissionAdmissionForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data["choice"] == "pass":
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.PREASSIGNMENT
            )
            # send authors admission passed email
            # mail_util = DirectMailUtil(
            #     "authors/admission_passed",
            #     submission=submission,
            #     comments_for_authors=form.cleaned_data["comments_for_authors"],
            # )
        else: # inadmissible, inform authors and set status to ADMISSION_FAILED
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.ADMISSION_FAILED
            )
            # send authors admission failed email
            mail_util = DirectMailUtil(
                "authors/admission_failed",
                submission=submission,
                comments_for_authors=form.cleaned_data["comments_for_authors"],
            )
            mail_util.send_mail()
        submission.refresh_from_db()
        # redirect to the edadmin page so that all is refreshed
        response = HttpResponse()
        response["HX-Redirect"] = reverse("submissions:pool:pool")
        return response
    context = {"submission": submission, "form": form,}
    return render(
        request,
        "edadmin/incoming/_hx_submission_admission_form.html",
        context,
    )
