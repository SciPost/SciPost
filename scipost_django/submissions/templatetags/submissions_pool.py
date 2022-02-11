__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import EditorialAssignment

register = template.Library()


@register.simple_tag
def get_editor_invitations(submission, user):
    """Check if the User invited to become EIC for Submission."""
    if not user.is_authenticated or not hasattr(user, "contributor"):
        return EditorialAssignment.objects.none()
    return EditorialAssignment.objects.filter(
        to__user=user, submission=submission
    ).invited()
