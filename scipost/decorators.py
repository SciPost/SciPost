__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Contributor


def has_contributor(user):
    """Requires user to be related to any Contributor."""
    try:
        user.contributor
        return True
    except Contributor.DoesNotExist:
        return False
