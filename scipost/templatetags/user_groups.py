from django import template

register = template.Library()


@register.simple_tag
def is_edcol_admin(user):
    """
    Assign template variable (boolean) to check if user is Editorial Administator.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Editorial Administrators').exists() or user.is_superuser


@register.simple_tag
def is_editor_in_charge(user, submission):
    """
    Assign template variable (boolean) to check if user is Editorial Administator.
    This assignment is limited to a certain context block!
    """
    if user.is_superuser:
        return True

    if not hasattr(user, 'contributor'):
        return False

    return submission.editor_in_charge == user.contributor
