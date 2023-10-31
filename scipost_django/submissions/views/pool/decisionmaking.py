__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from colleges.permissions import (
    fellowship_or_admin_required,
    is_edadmin,
    is_edadmin_or_senior_fellow,
)
from submissions.forms import RecommendationRemarkForm

from submissions.models import Submission, EICRecommendation
from submissions.constants import PUT_TO_VOTING


##########
# Voting #
##########


@login_required
@fellowship_or_admin_required()
def _hx_recommendation_voting_details_contents(
    request,
    identifier_w_vn_nr,
    rec_id,
):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)
    context = {
        "submission": submission,
        "recommendation": recommendation,
    }
    return render(
        request,
        (
            "submissions/pool/decisionmaking/"
            "_hx_recommendation_voting_details_contents.html"
        ),
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_recommendation_grant_voting_right(
    request,
    identifier_w_vn_nr,
    rec_id,
    spec_slug: str = None,
    nr: int = None,
    status: str = None,
    contributor_id: int = None,
):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)
    if contributor_id:
        recommendation.eligible_to_vote.add(contributor_id)
    elif spec_slug:
        conflicted_fellows_ids = [
            ci.fellowship.id for ci in submission.competing_interests.all()
        ]
        voting_fellows_to_add = (
            submission.fellows.active()
            .filter(
                contributor__profile__specialties__slug=spec_slug,
            )
            .exclude(
                contributor__profile__competing_interests__affected_submissions=submission,
            )
            .exclude(
                contributor__id__in=[
                    c.id for c in recommendation.eligible_to_vote.all()
                ],
            )
        )
        if status:
            if status == "senior":
                voting_fellows_to_add = voting_fellows_to_add.senior()
            elif status == "guest":
                voting_fellows_to_add = voting_fellows_to_add.guest()
        if nr and nr > 0:
            voting_fellows_to_add = voting_fellows_to_add.order_by("?")[:nr]
        recommendation.eligible_to_vote.add(
            *[f.contributor.id for f in voting_fellows_to_add.all()]
        )
    context = {
        "submission": submission,
        "recommendation": recommendation,
    }
    return render(
        request,
        (
            "submissions/pool/decisionmaking/"
            "_hx_recommendation_voting_details_contents.html"
        ),
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_recommendation_revoke_voting_right(
    request,
    identifier_w_vn_nr,
    rec_id,
    spec_slug: str = None,
    contributor_id: int = None,
):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)
    if spec_slug:
        voting_fellows_to_remove = recommendation.eligible_to_vote.filter(
            profile__specialties__slug=spec_slug,
        )
        recommendation.eligible_to_vote.remove(*voting_fellows_to_remove.all())
    elif contributor_id:
        recommendation.eligible_to_vote.remove(contributor_id)
    context = {
        "submission": submission,
        "recommendation": recommendation,
    }
    return render(
        request,
        (
            "submissions/pool/decisionmaking/"
            "_hx_recommendation_voting_details_contents.html"
        ),
        context,
    )


@login_required
@user_passes_test(is_edadmin)
def _hx_recommendation_open_voting(
    request,
    identifier_w_vn_nr,
    rec_id,
):
    submission = get_object_or_404(
        Submission.objects.in_pool(request.user, historical=True),
        preprint__identifier_w_vn_nr=identifier_w_vn_nr,
    )
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)
    Submission.objects.filter(pk=submission.id).update(
        status=Submission.IN_VOTING,
    )
    EICRecommendation.objects.filter(pk=recommendation.id).update(
        status=PUT_TO_VOTING,
    )
    return render(
        request,
        "submissions/pool/decisionmaking/_recommendations_and_voting.html",
        context={
            "submission": submission,
        },
    )


def _hx_recommendation_remarks(request, identifier_w_vn_nr, rec_id):
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)

    new_remark_form = RecommendationRemarkForm(
        request.POST or None,
        rec_id=rec_id,
        identifier_w_vn_nr=identifier_w_vn_nr,
        contributor=request.user.contributor,
    )

    if request.method == "POST" and new_remark_form.is_valid():
        new_remark_form.save()

    return render(
        request,
        "submissions/pool/decisionmaking/_hx_recommendation_remarks.html",
        context={"recommendation": recommendation, "form": new_remark_form},
    )
