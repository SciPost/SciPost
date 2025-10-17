__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import SubmissionClearance, ConflictOfInterest

register = template.Library()


@register.simple_tag
def get_profile_clearance(clearances, profile):
    """
    Return the SubmissionClearance for this Profile, or None.
    """
    return clearances.filter(profile=profile).first()


@register.simple_tag
def get_profile_conflicts_of_interest(conflicts_of_interest, profile):
    """
    Return all ConflictOfInterest for this Submission, Profile parameters.
    """
    from django.db.models import Q

    return conflicts_of_interest.filter(
        Q(profile=profile) | Q(related_profile=profile),
    )
