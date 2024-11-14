__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


def mailgun_webhook_is_signed(timestamp, token, signature):
    """
    Verify the signature of a mailgun webhook.
    """
    import hmac

    encoded_token = hmac.new(
        settings.MAILGUN_API_KEY.encode(),
        (timestamp + token).encode(),
        "sha256",
    ).hexdigest()

    return encoded_token == signature


def send_mailgun_alert_slack_message(event_data: dict):
    """
    Format mailgun event data and send an alert to Slack
    """
    import requests

    event = event_data.get("event", "unknown")
    reason = event_data.get("reason", "unknown")
    recipient = event_data.get("message", {}).get("headers", {}).get("to", "unknown")
    sender = event_data.get("message", {}).get("headers", {}).get("from", "unknown")
    subject = event_data.get("message", {}).get("headers", {}).get("subject", "unknown")
    error_description = event_data.get("delivery-status", {}).get("message", "unknown")

    # Ignore spam email directed to SciPost
    if "spam" in error_description and "scipost" in recipient:
        return

    message = f"[{event.upper()} / {reason}] {subject}\n{sender} -> {recipient}\nError: {error_description}"

    response = requests.post(
        settings.SLACK_WEBHOOK_URL_MAILGUN_ALERTS,
        json={"text": message},
        headers={"Content-type": "application/json"},
    )

    return response


@csrf_exempt
def mailgun_webhook(request):
    """
    Endpoint to receive POST requests for mailgun webhook.
    Executes custom integrations upon reception.
    """

    if request.method != "POST":
        return HttpResponse(status=405)

    data = json.loads(request.body)

    if "signature" not in data:
        return HttpResponse(status=400)

    # Verify signature, return 403 if invalid
    if not mailgun_webhook_is_signed(**data.get("signature")):
        return HttpResponse(status=403)

    # Apply custom integrations here
    event_data = data.get("event-data", {})
    send_mailgun_alert_slack_message(event_data)

    return HttpResponse(status=200)
