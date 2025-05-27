__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.contrib.auth import get_user_model

from helpdesk.constants import TICKET_PRIORITY_MEDIUM, TICKET_STATUS_UNASSIGNED
from helpdesk.models import Queue, Ticket
from ..utils import process_markup


register = template.Library()


@register.simple_tag(takes_context=True)
def automarkup(context, text, language_forced=None):
    markup = process_markup(text, language_forced=language_forced)
    if markup["errors"] and "request" in context and context["request"]:
        # Create a ticket (if not yet present) flagging the error for page's
        # url if automarkup called in template (so if context.request exists)
        markup_queue = Queue.objects.get(name="Markup")
        markup_firefighter, created = get_user_model().objects.get_or_create(
            username="markup-firefighter"
        )
        Ticket.objects.get_or_create(
            queue=markup_queue,
            title="Broken markup",
            description=f"{context['request'].get_full_path()}"
            f"\n\n{'\n'.join(markup.get('warnings', []))}"
            f"\n\n{markup.get('errors')}",
            defined_by=markup_firefighter,
            priority=TICKET_PRIORITY_MEDIUM,
            status=TICKET_STATUS_UNASSIGNED,
        )
    return markup["processed"]
