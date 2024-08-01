__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site

from common.utils.models import get_current_domain


def absolute_reverse(view_name, args=None, kwargs=None):
    """Return the absolute URL of a view, given its name and arguments."""
    from django.urls import reverse

    PROTOCOL = "https"
    domain = get_current_domain()
    reversed = reverse(view_name, args=args, kwargs=kwargs)

    return f"{PROTOCOL}://{domain}{reversed}"
