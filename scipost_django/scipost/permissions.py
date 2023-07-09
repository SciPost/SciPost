from functools import wraps

from django.contrib import messages
from django.http import HttpResponse

####################
# HTMX inline alerts
####################


class HTMXResponse(HttpResponse):
    tag = "primary"
    message = ""
    css_class = ""

    def __init__(self, *args, **kwargs):
        tag = kwargs.pop("tag", self.tag)
        message = args[0] if args else kwargs.pop("message", self.message)
        css_class = kwargs.pop("css_class", self.css_class)

        alert_html = f"""<div class="text-{tag} border border-{tag} p-3 {css_class}">
                {message}
            </div>"""

        super().__init__(alert_html, *args, **kwargs)


class HTMXPermissionsDenied(HTMXResponse):
    tag = "danger"
    message = "You do not have the required permissions."


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
