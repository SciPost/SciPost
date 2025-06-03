__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from guardian.shortcuts import get_objects_for_user

from colleges.permissions import is_edadmin
from journals.models import Publication
from mails.utils import DirectMailUtil
from pins.models import Note
from scipost.permissions import HTMXResponse
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

    if submission.on_hold:
        return HTMXResponse(
            "This submission is on hold and cannot be assessed for admissibility. Please take it off hold first.",
            tag="danger",
        )

    form = SubmissionAdmissibilityForm(request.POST or None, submission=submission)
    if form.is_valid():
        if form.cleaned_data["admissibility"] == "pass":
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.ADMISSIBLE
            )
            submission.add_event_for_edadmin("Submission admissibility passed")
        else:  # inadmissible, inform authors and set status to ADMISSION_FAILED
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.ADMISSION_FAILED
            )
            submission.add_event_for_edadmin("Submission admissibility failed")
            # send authors admission failed email
            mail_util = DirectMailUtil(
                "authors/admission_failed",
                submission=submission,
                rejection_email_text=form.cleaned_data["rejection_email_text"],
            )
            mail_util.send_mail()

            Note.objects.create(
                visibility=Note.VISIBILITY_INTERNAL,
                author=request.user.contributor,
                regarding_content_type=ContentType.objects.get_for_model(Submission),
                regarding_object_id=submission.id,
                title="Admissibility failed email sent",
                description="Email customized with:\n\n"
                + form.cleaned_data["rejection_email_text"],
            )
        submission.refresh_from_db()
        # trigger re-rendering of the details-contents div
        response = HttpResponse()
        response["HX-Trigger"] = f"submission-{submission.pk}-tab-edadmin-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
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

    submission_matches = [
        {
            "submission": s,
            "ratio_title": m["ratio_title"],
            "ratio_authors": m["ratio_authors"],
            "ratio_abstract": m["ratio_abstract"],
        }
        for m in submission.internal_plagiarism_matches.get("submission_matches", [])
        if (s := Submission.objects.filter(preprint__identifier_w_vn_nr=m["identifier_w_vn_nr"]).first())
    ]

    publication_matches = [
        {
            "publication": p,
            "ratio_title": m["ratio_title"],
            "ratio_authors": m["ratio_authors"],
            "ratio_abstract": m["ratio_abstract"],
        }
        for m in submission.internal_plagiarism_matches.get("publication_matches", [])
        if (p := Publication.objects.filter(doi_label=m["doi_label"]).first())
    ]

    context = {
        "submission": submission,
        "submission_matches": submission_matches,
        "publication_matches": publication_matches,
    }

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
    if form.is_valid():  # trigger re-rendering of details-contents div
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
    if form.is_valid():  # trigger re-rendering of details-contents div
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

    if submission.on_hold:
        return HTMXResponse(
            "This submission is on hold and cannot be admitted. Please take it off hold first.",
            tag="danger",
        )

    form = SubmissionAdmissionForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data["choice"] == "pass":
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.PREASSIGNMENT,
                checks_cleared_date=timezone.now(),
            )
            submission.add_event_for_edadmin("Submission admission passed")
            # send authors admission passed email
            # mail_util = DirectMailUtil(
            #     "authors/admission_passed",
            #     submission=submission,
            #     comments_for_authors=form.cleaned_data["comments_for_authors"],
            # )
        else:  # inadmissible, inform authors and set status to ADMISSION_FAILED
            Submission.objects.filter(pk=submission.id).update(
                status=Submission.ADMISSION_FAILED
            )
            submission.add_event_for_edadmin("Submission admission failed")
            # send authors admission failed email
            mail_util = DirectMailUtil(
                "authors/admission_failed",
                submission=submission,
                rejection_email_text=form.cleaned_data["rejection_email_text"],
            )
            mail_util.send_mail()

            Note.objects.create(
                visibility=Note.VISIBILITY_INTERNAL,
                author=request.user.contributor,
                regarding_content_type=ContentType.objects.get_for_model(Submission),
                regarding_object_id=submission.id,
                title="Admission failed email sent",
                description="Email customized with:\n\n"
                + form.cleaned_data["rejection_email_text"],
            )
        submission.refresh_from_db()
        response = HttpResponse()
        # trigger refresh of pool listing
        response["HX-Trigger-After-Settle"] = "search-conditions-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "edadmin/incoming/_hx_submission_admission_form.html",
        context,
    )
