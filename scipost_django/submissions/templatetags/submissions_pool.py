__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import EditorialAssignment, Qualification, Readiness

register = template.Library()


@register.simple_tag
def get_editor_invitations(submission, user):
    """Check if the User invited to become EIC for Submission."""
    if not user.is_authenticated or not hasattr(user, "contributor"):
        return EditorialAssignment.objects.none()
    return EditorialAssignment.objects.filter(
        to__user=user, submission=submission
    ).invited()


@register.simple_tag
def get_fellow_qualification(submission, fellow):
    """
    Return the Qualification for this Submission, Fellow parameters.
    """
    try:
        return submission.qualification_set.get(fellow=fellow)
    except Qualification.DoesNotExist:
        return None


@register.simple_tag
def get_fellow_qualification_expertise_level_display(submission, fellow):
    """
    Return the Qualification expertise_level display.
    """
    try:
        q = submission.qualification_set.get(fellow=fellow)
        return q.get_expertise_level_display()
    except Qualification.DoesNotExist:
        return ""


@register.simple_tag
def get_fellow_readiness(submission, fellow):
    """
    Return the Readiness for this Submission, Fellow parameters.
    """
    try:
        return submission.readiness_set.get(fellow=fellow)
    except Readiness.DoesNotExist:
        return None


@register.simple_tag
def get_fellow_readiness_status_display(submission, fellow):
    """
    Return the Readiness status display for this Submission, Fellow parameters.
    """
    try:
        r = submission.readiness_set.get(fellow=fellow)
        return r.get_status_display()
    except Readiness.DoesNotExist:
        return ""
