__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

from scipost.permissions import is_in_group


def fellowship_required():
    """Require user to have any Fellowship or Administrational permissions."""
    def test(u):
        if u.is_authenticated:
            if hasattr(u, 'contributor') and u.contributor.fellowships.exists():
                # Fellow
                return True
        raise PermissionDenied
    return user_passes_test(test)


def fellowship_or_admin_required():
    """Require user to have any Fellowship or Administrational permissions."""
    def test(u):
        if u.is_authenticated:
            if hasattr(u, 'contributor') and u.contributor.fellowships.exists():
                # Fellow
                return True

            if u.has_perm('scipost.can_oversee_refereeing'):
                # Administrator
                return True
        raise PermissionDenied
    return user_passes_test(test)
