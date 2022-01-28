__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

from scipost.permissions import is_in_group
from colleges.models import Fellowship


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
    """Require user to have any Fellowship or Administrative permissions."""
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


def is_edadmin_or_active_regular_or_senior_fellow(user):
    if not user.has_perm('scipost.can_run_pre_screening'):
        return Fellowship.objects.active().regular_or_senior(
        ).filter(contributor__user=user).exists()
    return True


def is_edadmin_or_senior_fellow(user):
    if not user.has_perm('scipost.can_run_pre_screening'):
        try:
            fellow = Fellowship.objects.active().get(contributor__user=user)
            return fellow.senior
        except:
            return False
    return True
