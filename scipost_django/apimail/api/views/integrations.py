__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import json
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.template import Template

from mails.models import MailLog
from mails.utils import DirectMailUtil


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from profiles.models import Profile

NestedStrDict = dict[str, "str | NestedStrDict"]


class MailgunEventData(NestedStrDict):
    """
    A class to wrap the event data dict and return "unknown" for missing keys.
    """

    def __init__(self, data: NestedStrDict):
        self.update(data)

    def __getitem__(self, key: str):
        key_parts = key.split(".")
        value = self.copy()
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

        requests.post(
            settings.SLACK_WEBHOOK_URL_MAILGUN_ALERTS,
            json={"text": message},
            headers={"Content-type": "application/json"},
        )


def alert_sender_on_perm_failure(event_data: MailgunEventData):
    """
    Send an email to the sender when a permanent failure occurs.
    """
    event = event_data["event"]
    reason = event_data["reason"]
    error_description = event_data["delivery-status.message"]
    message_id = event_data["message.headers.message-id"]

    if not (event == "failed" and (event_data.get("severity") == "permanent")):
        return

    if not (mail_log := MailLog.objects.filter(message_id=f"<{message_id}>").first()):
        raise ValueError(f"MailLog not found for message_id: {message_id}")

    if mail_log.mail_code in [
        "referees/invite_contributor_to_referee",
        "referees/invite_unregistered_to_referee",
    ]:
        invitation = mail_log.context.get("invitation").get_item()
        sender: "Profile" = invitation.submission.editor_in_charge.profile
        recipient: "Profile" = invitation.referee
        resend_instructions = Template(f"""<p>
            You are advised to cancel the existing invitation and send a new one to another email address from the 
            <a href="{reverse_lazy("submissions:editorial_page", kwargs={"identifier_w_vn_nr": invitation.submission.preprint.identifier_w_vn_nr})}">editorial page</a>.
            </p>""")
    else:
        # Temporarily disable other mail codes from sending delivery failure notifications
        return

    DirectMailUtil(
        mail_code="delivery_failure_notification",
        to_recipients=[sender.email],
        context={
            "mail_log": mail_log,
            "sender": sender,
            "recipient": recipient,
            "error_description": error_description,
            "reason": reason,
            "resend_instructions": resend_instructions,
        },
    )


@csrf_exempt
def mailgun_webhook(request):
    """
    Endpoint to receive POST requests for mailgun webhook.
    Executes custom integrations upon reception.
    """
    INTEGRATIONS = [
        send_mailgun_alert_slack_message,
        alert_sender_on_perm_failure,
    ]

    if request.method != "POST":
        return HttpResponse(status=405)

    data = json.loads(request.body)

    if "signature" not in data:
        return HttpResponse(status=400)

    # Verify signature, return 403 if invalid
    if not mailgun_webhook_is_signed(**data.get("signature")):
        return HttpResponse(status=403)

    event_data = MailgunEventData(data.get("event-data", {}))
    for integration in INTEGRATIONS:
        integration(event_data)

    return HttpResponse(status=200)
