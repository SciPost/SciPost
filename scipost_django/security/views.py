__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


@login_required
def security(request):
    return render(request, "security/security.html")


@login_required
def check_email_pwned(request, email=None):
    if email:
        if not request.user.is_superuser:
            raise PermissionDenied
    else:
        email = request.user.email

    hibp_base_url = "https://haveibeenpwned.com/api/v3"

    # Get breaches
    headers = {
        "hibp-api-key": settings.HAVE_I_BEEN_PWNED_API_KEY,
        "user-agent": "scipost",
    }
    breaches_params = {"truncateResponse": "false"}
    context = {
        "email": email,
    }
    breaches_url = "%s/%s/%s" % (hibp_base_url, "breachedaccount", email)
    breaches_r = requests.get(breaches_url, headers=headers, params=breaches_params)
    if breaches_r.status_code == 200:
        context["breaches_json"] = breaches_r.json()
    pastes_url = "%s/%s/%s" % (hibp_base_url, "pasteaccount", email)
    pastes_r = requests.get(pastes_url, headers=headers)
    if pastes_r.status_code == 200:
        context["pastes_json"] = pastes_r.json()
    return render(request, "security/check_email.html", context)
