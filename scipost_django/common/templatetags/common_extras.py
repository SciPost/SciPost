__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from django import template
from django.urls import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def action_url(context, **extra_kwargs):
    kwargs = context["action_url_base_kwargs"]
    kwargs.update(extra_kwargs)
    return reverse(context["action_url_name"], kwargs=kwargs)


@register.filter
def replace(text, args):
    if len(args.split("|")) != 2:
        return text
    a, b = args.split("|")
    return text.replace(a, b)


@register.filter
def rstrip_minutes(text):
    if "day" in text or "hour" in text:
        return re.split("[0-9]+\xa0minutes", text, 1)[0].rstrip(", ")
    return text


# Math
@register.filter
def int_divide(a, b):
    return a // b


@register.filter
def multiply(a, b):
    return a * b
