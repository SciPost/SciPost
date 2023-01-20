__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import EditorialAssignment, Qualification

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
        return Qualification.objects.get(submission=submission, fellow=fellow)
    except Qualification.DoesNotExist:
        return None


@register.simple_tag
def get_fellow_qualification_expertise_level_display(submission, fellow):
    """
    Return the Qualification for this Submission, Fellow parameters.
    """
    try:
        q = Qualification.objects.get(submission=submission, fellow=fellow)
        return q.get_expertise_level_display()
    except Qualification.DoesNotExist:
        return "?"
