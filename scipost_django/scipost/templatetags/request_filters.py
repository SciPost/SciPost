__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from django import template
from django.urls import reverse, NoReverseMatch

from urllib.parse import urlencode

from ..utils import build_absolute_uri_using_site

register = template.Library()


@register.simple_tag(takes_context=True)
def full_url(context, view_name, *args, **kwargs):
    rel_url = reverse(view_name, args=args, kwargs=kwargs)
    try:
        return context["request"].build_absolute_uri(rel_url)
    except KeyError:
        return build_absolute_uri_using_site(rel_url)


@register.simple_tag(takes_context=True)
def full_url_from_object(context, _object):
    rel_url = _object.get_absolute_url()
    try:
        return context["request"].build_absolute_uri(rel_url)
    except KeyError:
        return build_absolute_uri_using_site(rel_url)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context["request"].GET.dict()
    query.update(kwargs)
    return urlencode(query)


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = "^" + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context["request"].path
    if re.search(pattern, path):
        return "active"
    return ""


@register.simple_tag(takes_context=True)
def active_get_request(context, get_key, get_value):
    query = context["request"].GET.dict()
    return "active" if query.get(get_key) == str(get_value) else ""
