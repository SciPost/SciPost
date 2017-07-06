from .models import Contributor


def has_contributor(user):
    """Requires user to be related to any Contributor."""
    try:
        user.contributor
        return True
    except Contributor.DoesNotExist:
        return False
