__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

NestedStrDict = dict[str, "str | NestedStrDict"]


class MailgunEventData(NestedStrDict):
    """
    A class to wrap the event data dict and return "unknown" for missing keys.
    """

    def __init__(self, data: NestedStrDict):
        self.data = data

    def __getitem__(self, key: str):
        key_parts = key.split(".")
        value = self.data
        for part in key_parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return "unknown"

        if isinstance(value, dict):
            return MailgunEventData(value)
        else:
            return value


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


def send_mailgun_alert_slack_message(event_data: MailgunEventData):
    """
    Format mailgun event data and send an alert to Slack
    """
    import requests

    event = event_data["event"]
    reason = event_data["reason"]
    recipient = event_data["message.headers.to"]
    sender = event_data["message.headers.from"]
    subject = event_data["message.headers.subject"]
    error_description = event_data["delivery-status.message"]

    # Ignore spam email directed to SciPost
    bad_keywords = ["spam", "scam", "phishing", "fraud", "viral"]
    error_contains_keyword = any(k in error_description.lower() for k in bad_keywords)
    if "scipost" in recipient and error_contains_keyword:
        return

    if event == "failed" and (event_data.get("severity", "unknown") == "permanent"):
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
    event_data = MailgunEventData(data.get("event-data", {}))
    send_mailgun_alert_slack_message(event_data)

    return HttpResponse(status=200)
