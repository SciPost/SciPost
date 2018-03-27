import re

from django import template
from django.core.urlresolvers import reverse, NoReverseMatch

from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urlencode(query)


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = '^' + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].path
    if re.search(pattern, path):
        return 'active'
    return ''


@register.simple_tag(takes_context=True)
def active_get_request(context, get_key, get_value):
    query = context['request'].GET.dict()
    return 'active' if query.get(get_key) == str(get_value) else ''
