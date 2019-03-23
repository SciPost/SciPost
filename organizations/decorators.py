__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Contact


def has_contact(user):
    """Requires user to be related to a Contact."""
    try:
        user.org_contact
        return True
    except (Contact.DoesNotExist, AttributeError):
        return False
