__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template


register = template.Library()


@register.filter
def has_editor(submission):
    """Return if submission either has editor."""
    return submission.editor_in_charge is not None


@register.filter
def has_preassignments(submission):
    """Return if submission has editor pre-assignments/invitations."""
    return submission.editorial_assignments.exists()
