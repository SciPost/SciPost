__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import user_passes_test
from scipost.views import HTMXPermissionsDenied
from functools import wraps
from django.contrib import messages


def is_production_user():
    """Requires user to be a ProductionUser."""

    def test(u):
        if u.is_authenticated:
            if hasattr(u, "production_user") and u.production_user:
                return True
        return False

    return user_passes_test(test)


def permission_required_htmx(
    perm,
    message="You do not have the required permissions.",
    **message_kwargs,
):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if isinstance(perm, str):
                perms = (perm,)
            else:
                perms = perm

            if request.user.has_perms(perms):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, message)
                return HTMXPermissionsDenied(message, **message_kwargs)

        return _wrapped_view

    return decorator
