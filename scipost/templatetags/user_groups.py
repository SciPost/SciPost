from django import template

register = template.Library()


@register.simple_tag
def is_edcol_admin(user):
    """
    Assign template variable (boolean) to check if user is Editorial Administator.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name='Editorial Administrators').exists() or user.is_superuser
