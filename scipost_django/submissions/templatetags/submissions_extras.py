__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..constants import (
    DECISION_FIXED,
    REPORT_PUBLISH_1,
    REPORT_PUBLISH_2,
    REPORT_PUBLISH_3,
)
from ..models import Submission, EICRecommendation

register = template.Library()


@register.filter
def filter_for_submission(qs, submission):
    """Filter (any) query with the given Submission."""
    return qs.filter(submission=submission)


@register.filter
def is_in_submission_fellowship(user, submission):
    return submission.fellows.filter(contributor__user=user).exists()


@register.filter
def is_editor_of_submission(user, submission):
    return submission.editor_in_charge and submission.editor_in_charge.user == user


@register.filter
def is_possible_author_of_submission(user, submission):
    """Check if User may be related to the Submission as author."""
    if not isinstance(submission, Submission):
        return False

    if not user.is_authenticated:
        return False

    if submission.authors.filter(user=user).exists():
        # User explicitly assigned author.
        return True

    if submission.authors_false_claims.filter(user=user).exists():
        # User explicitly dissociated from the Submission.
        return False

    # Last resort: last name check
    return user.last_name in submission.author_list


@register.filter
def is_viewable_by_authors(recommendation):
    """Check if the EICRecommendation is viewable by the authors of the Submission."""
    if not isinstance(recommendation, EICRecommendation):
        return False
    return recommendation.status == DECISION_FIXED


@register.filter
def user_can_vote(recommendation, user):
    return recommendation.eligible_to_vote.filter(user=user).exists()


@register.filter
def user_is_referee(submission, user):
    """Check if the User is invited to be Referee of the Submission."""
    if not user.is_authenticated:
        return False
    return submission.referee_invitations.filter(
        referee=user.contributor.profile
    ).exists()


@register.filter
def citation(citable):
    return citable.citation


@register.filter
def Tier(recommendation):
    if recommendation.recommendation == REPORT_PUBLISH_1:
        return "Tier I"
    elif recommendation.recommendation == REPORT_PUBLISH_2:
        return "Tier II"
    elif recommendation.recommendation == REPORT_PUBLISH_3:
        return "Tier III"
    else:
        return "unknown Tier"
