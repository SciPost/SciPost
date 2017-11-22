from django.contrib.auth.decorators import user_passes_test


def fellowship_required():
    """Require user to have any Fellowship."""
    def test(u):
        if u.is_authenticated():
            if hasattr(u, 'contributor') and u.contributor.fellowships.exists():
                return True
        return False
    return user_passes_test(test)
