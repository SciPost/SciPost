__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import user_passes_test

from .models import Contributor


def has_contributor(user):
    """Require user to be related to any Contributor."""
    try:
        user.contributor
        return True
    except (Contributor.DoesNotExist, AttributeError):
        return False


def is_contributor_user():
    """Decorator checking if user is related to any Contributor."""
    def test(u):
        if u.is_authenticated:
            return has_contributor(u)
        return False
    return user_passes_test(test)
