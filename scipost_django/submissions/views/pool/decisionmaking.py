__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from colleges.permissions import (
    fellowship_or_admin_required,
    is_edadmin,
    is_edadmin_or_senior_fellow,
)
from ethics.models import ConflictOfInterest
from scipost.permissions import HTMXResponse
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
    submission_authors = submission.author_profiles.values_list("profile", flat=True)
    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)
    context = {
        "submission": submission,
        "recommendation": recommendation,
        "submission_fellows": submission.fellows.all()
        .select_related_contributor__dbuser_and_profile()
        .prefetch_related(
            Prefetch(
                "contributor__profile__conflicts_of_interest",
                queryset=ConflictOfInterest.objects.valid_on_date()
                .filter(related_profile__in=submission_authors)
                .annot_submission_exempted(submission),
                to_attr="submission_conflicts_of_interest",
            ),
            Prefetch(
                "contributor__profile__related_conflicts_of_interest",
                queryset=ConflictOfInterest.objects.valid_on_date()
                .filter(profile__in=submission_authors)
                .annot_submission_exempted(submission),
                to_attr="submission_conflicts_of_interest_related",
            ),
        ),
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
        voting_fellows_to_add = (
            submission.fellows.active()
            .filter(contributor__profile__specialties__slug=spec_slug)
            .without_conflicts_of_interest_against_submission_authors_of(submission)
            .exclude(contributor__id__in=recommendation.eligible_to_vote.all())
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

    return _hx_recommendation_voting_details_contents(
        request, identifier_w_vn_nr, rec_id
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

    return _hx_recommendation_voting_details_contents(
        request, identifier_w_vn_nr, rec_id
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

    # Guard against on-hold submissions
    if submission.on_hold:
        return HTMXResponse(
            "The submission is on hold and cannot be put to voting.",
            tag="danger",
        )

    recommendation = get_object_or_404(EICRecommendation, pk=rec_id)
    Submission.objects.filter(pk=submission.id).update(
        status=Submission.IN_VOTING,
    )
    EICRecommendation.objects.filter(pk=recommendation.id).update(
        status=PUT_TO_VOTING,
    )
    submission.add_event_for_edadmin(
        "Voting on recommendation "
        f"{recommendation.get_recommendation_short_display()} "
        f"for {recommendation.get_for_journal_display()} "
        "started"
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
        new_remark_form = RecommendationRemarkForm(
            rec_id=rec_id,
            identifier_w_vn_nr=identifier_w_vn_nr,
            contributor=request.user.contributor,
        )

    return render(
        request,
        "submissions/pool/decisionmaking/_hx_recommendation_remarks.html",
        context={"recommendation": recommendation, "form": new_remark_form},
    )
