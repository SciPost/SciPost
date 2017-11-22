from django.contrib.auth.decorators import user_passes_test


def fellowship_required():
    """
    Require user to have any Fellowship or Administrational permissions.
    """
    def test(u):
        if u.is_authenticated():
            if hasattr(u, 'contributor') and u.contributor.fellowships.exists():
                # Fellow
                return True

            if u.has_perm('scipost.can_view_pool'):
                # Administrator
                return True
        return False
    return user_passes_test(test)
