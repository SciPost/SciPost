__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import SubmissionClearance, CompetingInterest

register = template.Library()


@register.simple_tag
def get_profile_clearance(submission, profile):
    """
    Return the SubmissionClearance for this Profile, or None.
    """
    return SubmissionClearance.objects.filter(
        submission=submission,
        profile=profile,
    ).first()


@register.simple_tag
def get_profile_competing_interests(submission, profile):
    """
    Return all CompetingInterest for this Submission, Profile parameters.
    """
    from django.db.models import Q
    return CompetingInterest.objects.filter(affected_submissions=submission).filter(
        Q(profile=profile) | Q(related_profile=profile),
    )
