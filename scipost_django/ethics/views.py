__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from multiprocessing import Pool
import time
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models.functions import Coalesce, Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from ethics.models import Coauthorship, SubmissionClearance, ConflictOfInterest
from ethics.forms import (
    SubmissionConflictOfInterestForm,
    SubmissionConflictOfInterestTableRowForm,
)

from colleges.permissions import is_edadmin
from colleges.models.fellowship import Fellowship
from ethics.tasks import (
    celery_fetch_potential_coauthorships_for_profile_and_submission_authors,
)
from preprints.servers.crossref import CrossrefServer
from preprints.servers.server import PreprintServer
from profiles.models import Profile
from scipost.permissions import HTMXResponse, permission_required_htmx
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
    conflict_of_interest = (
        ConflictOfInterest.objects.all()
        .involving_profile(request.user.contributor.profile)
        .involving_any_submission_author_of(submission)
        .valid_on_date()
        .first()
    )
    context = {
        "submission": submission,
        "clearance": clearance,
        "conflict_of_interest": conflict_of_interest,
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
    response = HttpResponse()
    response["HX-Trigger"] = "coi-clearance-asserted"
    return response


@login_required
def _hx_submission_clearance_revoke(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    SubmissionClearance.objects.filter(
        profile=request.user.contributor.profile,
        submission=submission,
        asserted_by=request.user.contributor,  # can only revoke own clearances
    ).delete()
    return redirect(
        reverse(
            "submissions:pool:_hx_radio_appraisal_form",
            kwargs={"identifier_w_vn_nr": identifier_w_vn_nr},
        )
    )


#######################
# Conflicts of Interest #
#######################


@login_required
def _hx_submission_conflict_of_interest_form(request, identifier_w_vn_nr):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    initial = {
        "profile": request.user.contributor.profile,
        "declared_by": request.user.contributor,
    }
    if submission.author_profiles.count() == 1:
        initial["related_profile"] = submission.author_profiles.first().profile
    form = SubmissionConflictOfInterestForm(
        request.POST or None,
        submission=submission,
        initial=initial,
    )
    if form.is_valid():
        form.save()
        response = HttpResponse()
        response["HX-Trigger-After-Settle"] = "search-conditions-updated"
        return response
    context = {
        "submission": submission,
        "form": form,
    }
    return render(
        request,
        "ethics/_hx_submission_conflict_of_interest_form.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_conflict_of_interest_delete(request, identifier_w_vn_nr, pk):
    submission = get_object_or_404(
        Submission,
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    conflict_of_interest = get_object_or_404(ConflictOfInterest, pk=pk)
    conflict_of_interest.delete()

    context = {
        "submission": submission,
    }
    response = render(
        request,
        "submissions/pool/_submission_fellows.html",
        context,
    )
    response["HX-Retarget"] = f"#submission-{submission.id}-fellows-details"
    return response


@login_required
@user_passes_test(is_edadmin)
def _hx_submission_conflict_of_interest_create(
    request, identifier_w_vn_nr, fellowship_id
):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    fellowship = get_object_or_404(Fellowship, id=fellowship_id)
    initial = {
        "profile": fellowship.contributor.profile,
        "declared_by": request.user.contributor,
    }
    if submission.author_profiles.count() == 1:
        initial["related_profile"] = submission.author_profiles.first().profile
    form = SubmissionConflictOfInterestTableRowForm(
        request.POST or None,
        submission=submission,
        initial=initial,
    )
    if form.is_valid():
        form.save()
        response = render(
            request,
            "submissions/pool/_submission_fellows.html",
            context={"submission": submission},
        )
        response["HX-Retarget"] = f"#submission-{submission.id}-fellows-details"
        return response

    context = {
        "submission": submission,
        "form": form,
        "identifier_w_vn_nr": identifier_w_vn_nr,
        "fellowship_id": fellowship_id,
    }
    return render(
        request,
        "ethics/_hx_submission_conflict_of_interest_create.html",
        context,
    )


@login_required
@permission_required_htmx("scipost.can_verify_coauthorships")
@permission_required_htmx("scipost.can_promote_coauthorships_to_conflicts_of_interest")
def _hx_coauthorship_verify(request, pk):
    try:
        coauthorship = Coauthorship.objects.get(pk=pk)
        coauthorship.verify(request.user.contributor)
        conflict_of_interest = ConflictOfInterest.from_coauthorship(coauthorship)
        conflict_of_interest.save()
        coauthorship.conflict_of_interest = conflict_of_interest
        coauthorship.save()
    except Coauthorship.DoesNotExist:
        return HTMXResponse("Coauthorship not found", tag="danger")

    response = TemplateResponse(
        request,
        "submissions/admin/_coauthorship_verification.html",
        context={"coauthorship": coauthorship},
    )
    return response


@login_required
@permission_required_htmx("scipost.can_verify_coauthorships")
def _hx_coauthorship_deprecate(request, pk):
    try:
        coauthorship = Coauthorship.objects.get(pk=pk)
        coauthorship.deprecate(request.user.contributor)
    except Coauthorship.DoesNotExist:
        return HTMXResponse("Coauthorship not found", tag="danger")

    response = TemplateResponse(
        request,
        "submissions/admin/_coauthorship_verification.html",
        context={"coauthorship": coauthorship},
    )
    return response


@login_required
@permission_required_htmx("scipost.can_verify_coauthorships")
@permission_required_htmx("scipost.can_promote_coauthorships_to_conflicts_of_interest")
def _hx_coauthorship_reset_status(request, pk):
    try:
        coauthorship = Coauthorship.objects.get(pk=pk)
        coauthorship.reset_status(request.user.contributor)
        if coi := coauthorship.conflict_of_interest:
            coi.delete()

    except Coauthorship.DoesNotExist:
        return HTMXResponse("Coauthorship not found", tag="danger")

    response = TemplateResponse(
        request,
        "submissions/admin/_coauthorship_verification.html",
        context={"coauthorship": coauthorship},
    )
    return response


@login_required
@permission_required_htmx("scipost.can_view_coauthorships")
def _hx_list_coauthorships_for_submission_authors(
    request, identifier_w_vn_nr, profile_pk
):
    submission = Submission.objects.filter(
        preprint__identifier_w_vn_nr=identifier_w_vn_nr
    ).first()
    profile = Profile.objects.filter(pk=profile_pk).first()
    if not submission or not profile:
        return HTMXResponse("Submission or profile not found", tag="danger")

    coauthorships = (
        Coauthorship.objects.involving_profile(profile)
        .involving_any_author_of(submission)
        .select_related("profile", "coauthor", "work")
    )

    context = {
        "submission": submission,
        "profile": profile,
        "coauthorships": coauthorships,
    }
    return render(request, "submissions/admin/_coauthorships.html", context)


@login_required
@permission_required_htmx("scipost.can_fetch_coauthorships")
@transaction.atomic
def _hx_fetch_coauthorships_for_submission_authors(
    request, identifier_w_vn_nr, profile_pk
):
    submission = Submission.objects.filter(
        preprint__identifier_w_vn_nr=identifier_w_vn_nr
    ).first()
    profile = Profile.objects.filter(pk=profile_pk).first()
    if not submission or not profile:
        return HTMXResponse("Submission or profile not found", tag="danger")

    preprint_servers = submission.get_coauthorship_preprint_servers()
    try:
        task = celery_fetch_potential_coauthorships_for_profile_and_submission_authors.delay(
            profile.id,
            submission.id,
            preprint_servers=preprint_servers,
        )
    except Exception as e:
        return HTMXResponse(f"Error starting task: {e}", tag="danger")

    # Give the task a moment to start and register in the backend
    time.sleep(2)

    return redirect(
        reverse("common:hx_celery_task_status", kwargs={"task_id": task.id})
    )
