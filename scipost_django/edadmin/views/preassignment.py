__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from colleges.permissions import is_edadmin
from profiles.models import Profile
from profiles.forms import ProfileDynSelForm
from submissions.models import Submission, SubmissionAuthorProfile


###########################
# Author Profile matching #
###########################
@login_required
@user_passes_test(is_edadmin)
def _hx_author_profiles_details_summary(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    matches = submission.author_profiles.exclude(profile__isnull=True).count()
    context = {
        "submission": submission,
        "matches": matches,
    }
    return render(
        request,
        "edadmin/preassignment/_hx_author_profiles_details_summary.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin)
def _hx_author_profiles_details_contents(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    matches_list = [ (
        author_string,
        index + 1,
        submission.author_profiles.filter(
            order=index + 1,
            profile__isnull=False,
        ).first(),
    ) for index, author_string in enumerate(submission.authors_as_list) ]

    context = {
        "submission": submission,
        "matches_list": matches_list,
    }
    return render(
        request,
        "edadmin/preassignment/_hx_author_profiles_details_contents.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin)
def _hx_author_profile_row(request, identifier_w_vn_nr, order: int):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    author_string = submission.authors_as_list[order-1]
    profile = submission.author_profiles.filter(
            order=order,
            profile__isnull=False,
    ).first()
    context = {
        "submission": submission,
        "author_string": author_string,
        "order": order,
        "profile": profile,
    }
    if profile is None:
        profile_dynsel_form = ProfileDynSelForm(
            initial={
                "q": author_string.rpartition(". ")[2],
                "action_url_name": "edadmin:preassignment:_hx_author_profile_action",
                "action_url_base_kwargs": {
                    "identifier_w_vn_nr": identifier_w_vn_nr,
                    "order": order,
                    "action": "match",
                },
                "action_target_element_id":
                f"submission-{submission.pk}-author-profile-row-{order}",
                "action_target_swap": "outerHTML",
            }
        )
        context["profile_dynsel_form"] = profile_dynsel_form
    response = render(
        request,
        "edadmin/preassignment/_hx_author_profile_row.html",
        context,
    )
    response["HX-Trigger-After-Settle"] = f"submission-{submission.pk}-author-profiles-details-updated"
    return response


@login_required
@user_passes_test(is_edadmin)
def _hx_author_profile_action(
        request,
        identifier_w_vn_nr,
        order,
        profile_id,
        action: str="match",
):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    profile = get_object_or_404(Profile, pk=profile_id)
    author_profile, created = SubmissionAuthorProfile.objects.get_or_create(
        submission=submission,
        order=order,
    )
    if action == "match":
        author_profile.profile = profile
    elif action == "unmatch":
        author_profile.profile = None
    author_profile.save()
    response = redirect(
        reverse(
            "edadmin:preassignment:_hx_author_profile_row",
            kwargs={
                "identifier_w_vn_nr": identifier_w_vn_nr,
                "order": order,
            }
        )
    )
    return response
