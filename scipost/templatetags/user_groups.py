__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


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
def is_scipost_admin(user):
    """
    Assign template variable (boolean) to check if user is SciPost Administrator.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='SciPost Administrators').exists() or user.is_superuser


@register.simple_tag
def is_editorial_college(user):
    """
    Assign template variable (boolean) to check if user is member of Editorial College group.

    !!!
    This filter should actually be dynamic, not checking the permissions group but the current
    active Fellowship instances for the user.
    !!!

    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Editorial College').exists() or user.is_superuser


@register.simple_tag
def is_advisory_board(user):
    """
    Assign template variable (boolean) to check if user is in Advisory Board.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Advisory Board').exists() or user.is_superuser


@register.simple_tag
def is_vetting_editor(user):
    """
    Assign template variable (boolean) to check if user is in Vetting Editor.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Vetting Editors').exists() or user.is_superuser


@register.simple_tag
def is_ambassador(user):
    """
    Assign template variable (boolean) to check if user is Ambassador.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Ambassadors').exists() or user.is_superuser


@register.simple_tag
def is_junior_ambassador(user):
    """
    Assign template variable (boolean) to check if user is Junior Ambassador.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Junior Ambassadors').exists() or user.is_superuser


@register.simple_tag
def is_registered_contributor(user):
    """
    Assign template variable (boolean) to check if user is Registered Contributor.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Registered Contributors').exists() or user.is_superuser


@register.simple_tag
def is_tester(user):
    """
    Assign template variable (boolean) to check if user is Tester.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Testers').exists() or user.is_superuser


@register.simple_tag
def is_production_officer(user):
    """
    Assign template variable (boolean) to check if user is Production Officer.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Production Officers').exists() or user.is_superuser


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
