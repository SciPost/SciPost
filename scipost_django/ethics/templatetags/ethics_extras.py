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
