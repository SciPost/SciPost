__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render

from guardian.shortcuts import get_objects_for_user

from colleges.permissions import is_edadmin
from submissions.models import Submission
from submissions.forms import iThenticateReportForm


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
def _hx_plagiarism_internal(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    context = {"submission_matches": [], "publication_matches": []}
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
    form = InternalPlagiarismAssessmentForm(request.POST or None)
    if form.is_valid():
        form.save()


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
