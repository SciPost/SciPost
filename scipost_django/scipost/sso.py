__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import base64
import hmac
import hashlib
from urllib import parse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.conf import settings


@login_required
def discourse(request):
    """
    Callback for the Discourse instance at disc.scipost.org.

    Make sure to set `DISCOURSE_BASE_URL` and `DISCOURSE_SSO_SECRET` in settings.py

    Taken from https://gist.github.com/alee/3c6161809ef78966454e434a8ed350d1

    Code was originally adapted from https://meta.discourse.org/t/sso-example-for-django/14258 but that discussion topic has been removed.
    """
    payload = request.GET.get("sso")
    signature = request.GET.get("sig")

    if None in [payload, signature]:
        return HttpResponseBadRequest(
            "No SSO payload or signature. Please contact techsupport if this problem persists."
        )

    # Validate the payload

    payload = bytes(parse.unquote(payload), encoding="utf-8")
    decoded = base64.decodebytes(payload).decode("utf-8")
    if len(payload) == 0 or "nonce" not in decoded:
        return HttpResponseBadRequest(
            "Invalid payload. Please contact support if this problem persists."
        )

    key = bytes(settings.DISCOURSE_SSO_SECRET, encoding="utf-8")  # must not be unicode
    h = hmac.new(key, payload, digestmod=hashlib.sha256)
    this_signature = h.hexdigest()

    if not hmac.compare_digest(this_signature, signature):
        return HttpResponseBadRequest(
            "Invalid payload. Please contact support if this problem persists."
        )

    # Build the return payload
    qs = parse.parse_qs(decoded)
    user = request.user
    params = {
        "nonce": qs["nonce"][0],
        "email": user.email,
        "external_id": user.id,
        "username": user.username,
        "require_activation": "true",
        "name": user.get_full_name(),
    }

    return_payload = base64.encodebytes(bytes(parse.urlencode(params), "utf-8"))
    h = hmac.new(key, return_payload, digestmod=hashlib.sha256)
    query_string = parse.urlencode({"sso": return_payload, "sig": h.hexdigest()})

    # Redirect back to Discourse
    discourse_sso_url = (
        f"{settings.DISCOURSE_BASE_URL}/session/sso_login?{query_string}"
    )
    return HttpResponseRedirect(discourse_sso_url)
