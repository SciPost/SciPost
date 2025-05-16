__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from functools import wraps
from django import template

from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()

register = template.Library()


def guard_real_user(fn):
    """
    Decorator to ensure that the "user" argument is of type User.
    """

    @wraps(fn)
    def wrapper(user, *args, **kwargs):
        if not isinstance(user, USER_MODEL):
            return False
        return fn(user, *args, **kwargs)

    return wrapper


@register.simple_tag
@guard_real_user
def is_ed_admin(user):
    """
    Assign template variable (boolean) to check if user is Editorial Administator.
    This assignment is limited to a certain context block!
    """
    return (
        user.groups.filter(name="Editorial Administrators").exists()
        or user.is_superuser
    )


@register.simple_tag
@guard_real_user
def is_scipost_admin(user):
    """
    Assign template variable (boolean) to check if user is SciPost Administrator.
    This assignment is limited to a certain context block!
    """
    return (
        user.groups.filter(name="SciPost Administrators").exists() or user.is_superuser
    )


@register.simple_tag
@guard_real_user
def is_financial_admin(user):
    """
    Assign template variable (boolean) to check if user is Financial Administrator.
    This assignment is limited to a certain context block!
    """
    return (
        user.groups.filter(name="Financial Administrators").exists()
        or user.is_superuser
    )


@register.simple_tag
@guard_real_user
def is_active_fellow(user):
    """
    Assign template variable (boolean) to check if user is member of Editorial College group.
    """
    if not hasattr(user, "contributor"):
        return False
    return user.contributor.is_active_fellow


@register.simple_tag
@guard_real_user
def is_advisory_board(user):
    """
    Assign template variable (boolean) to check if user is in Advisory Board.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Advisory Board").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def is_vetting_editor(user):
    """
    Assign template variable (boolean) to check if user is in Vetting Editor.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Vetting Editors").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def is_ambassador(user):
    """
    Assign template variable (boolean) to check if user is Ambassador.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Ambassadors").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def is_junior_ambassador(user):
    """
    Assign template variable (boolean) to check if user is Junior Ambassador.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Junior Ambassadors").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def is_registered_contributor(user):
    """
    Assign template variable (boolean) to check if user is Registered Contributor.
    This assignment is limited to a certain context block!
    """
    return (
        user.groups.filter(name="Registered Contributors").exists() or user.is_superuser
    )


@register.simple_tag
@guard_real_user
def is_tester(user):
    """
    Assign template variable (boolean) to check if user is Tester.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Testers").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def is_production_officer(user):
    """
    Assign template variable (boolean) to check if user is Production Officer.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Production Officers").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def is_editor_in_charge(user, submission):
    """
    Assign template variable (boolean) to check if user is Editorial Administator.
    This assignment is limited to a certain context block!
    """
    if user.is_superuser:
        return True

    if not hasattr(user, "contributor"):
        return False

    return submission.editor_in_charge == user.contributor


@register.simple_tag
@guard_real_user
def is_pub_officer(user):
    """
    Assign template variable (boolean) to check if user is Publication Officer.
    This assignment is limited to a certain context block!
    """
    return user.groups.filter(name="Publication Officers").exists() or user.is_superuser


@register.simple_tag
@guard_real_user
def recommend_new_totp_device(user):
    """
    Check if User has no TOTPDevice, but still has a high level of information access.
    """
    if user.devices.exists():
        return False
    if user.is_superuser:
        return True
    if user.contributor.fellowships.exists():
        return True
    return user.groups.filter(
        name__in=[
            "Editorial Administrators",
            "SciPost Administrators",
            "Advisory Board",
            "Financial Administrators",
            "Vetting Editors",
            "Editorial College",
        ]
    ).exists()
