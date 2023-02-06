__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.urls import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def topic_dynsel_action_url(context, topic):
    kwargs = context["action_url_base_kwargs"]
    kwargs["topic_slug"] = topic.slug
    return reverse(context["action_url_name"], kwargs=kwargs)
