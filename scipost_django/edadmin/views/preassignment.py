__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone

from colleges.permissions import is_edadmin
from mails.utils import DirectMailUtil
from profiles.models import Profile
from profiles.forms import ProfileDynSelForm
from submissions.models import Submission, SubmissionAuthorProfile

from edadmin.forms import SubmissionPreassignmentDecisionForm


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
    matches_list = [
        (
            author_string,
            index + 1,
            submission.author_profiles.filter(
                order=index + 1,
                profile__isnull=False,
            ).first(),
        )
        for index, author_string in enumerate(submission.authors_as_list)
    ]

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
    author_string = submission.authors_as_list[order - 1]
    profile = submission.author_profiles.filter(
        order=order,
        profile__isnull=False,
    ).first()

    submission_specialties_serialized = ",".join([str(s.id) for s in submission.specialties.all()])
    author_first_name_guess, *author_last_name_guess = author_string.split(" ", 1)
    context = {
        "submission": submission,
        "author_string": author_string,
        "submission_specialties_serialized": submission_specialties_serialized,
        "author_first_name_guess": author_first_name_guess,
        "author_last_name_guess": author_last_name_guess[0] if author_last_name_guess else "",
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
                "action_target_element_id": f"submission-{submission.pk}-author-profile-row-{order}",
                "action_target_swap": "outerHTML",
            }
        )
        context["profile_dynsel_form"] = profile_dynsel_form
    response = render(
        request,
        "edadmin/preassignment/_hx_author_profile_row.html",
        context,
    )
    response["HX-Trigger-After-Settle"] = (
        f"submission-{submission.pk}-author-profiles-details-updated"
    )
    return response


@login_required
@user_passes_test(is_edadmin)
def _hx_author_profile_action(
    request,
    identifier_w_vn_nr,
    order,
    profile_id,
    action: str = "match",
):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    author_profile, created = SubmissionAuthorProfile.objects.get_or_create(
        submission=submission,
        order=order,
    )
    if action == "match":
        profile = get_object_or_404(Profile, pk=profile_id)

        potential_duplicate_fellow = (
            Profile.objects.potential_duplicates_of(profile)
            .annotate(is_fellow=Q(contributor__fellowships__isnull=False))
            .filter(is_fellow=True)
            .first()
        )
        if potential_duplicate_fellow:
            messages.error(
                request,
                "This profile has potential duplicates which belong to Fellows. Please "
                f'<a href="{reverse("profiles:duplicates", args=(profile.id, potential_duplicate_fellow.id))}">resolve the duplicates</a> '
                "before matching. ",
            )
            author_profile.profile = None
        else:
            author_profile.profile = profile
            # add Submission's topics to profile:
            profile.topics.add(*submission.topics.all())
    elif action == "unmatch":
        author_profile.profile = None
    author_profile.save()
    response = redirect(
        reverse(
            "edadmin:preassignment:_hx_author_profile_row",
            kwargs={
                "identifier_w_vn_nr": identifier_w_vn_nr,
                "order": order,
            },
        )
    )
    return response


##########################
# Preassignment decision #
##########################


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_preassignment_decision(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr
    )
    form = SubmissionPreassignmentDecisionForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data["choice"] == "pass":
            submission.status = Submission.SEEKING_ASSIGNMENT
            submission.assignment_deadline = (
                timezone.now() + submission.submitted_to.assignment_period
            )
            submission.save()

            submission.add_event_for_edadmin("Submission preassignment passed")
            # send authors admission passed email
            mail_util = DirectMailUtil(
                "authors/preassignment_completed",
                submission=submission,
                comments_for_authors=form.cleaned_data["comments_for_authors"],
            )

            # Reset the fellowship for the submission
            # This is done to remove authors matched during preassignment
            submission.fellows.set(submission.get_default_fellowship())

        else:  # inadmissible, inform authors and set status to PREASSIGNMENT_FAILED
            submission.status = Submission.PREASSIGNMENT_FAILED
            submission.save()
            submission.add_event_for_edadmin("Submission preassignment failed")
            # send authors admission failed email
            mail_util = DirectMailUtil(
                "authors/preassignment_failed",
                submission=submission,
                comments_for_authors=form.cleaned_data["comments_for_authors"],
            )
        mail_util.send_mail()
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
        "edadmin/preassignment/_hx_submission_preassignment_decision.html",
        context,
    )
