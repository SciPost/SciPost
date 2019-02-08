__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.utils.html import escape
from django.utils.text import normalize_newlines
from django.utils.safestring import SafeData, mark_safe

register = template.Library()


@register.filter(is_safe=False, needs_autoescape=True)
def linebreaktex(value, autoescape=True):
    """
    Convert all newlines in a piece of plain text to HTML line breaks
    """
    autoescape = autoescape and not isinstance(value, SafeData)
    value = normalize_newlines(value)
    if autoescape:
        value = escape(value)
    return mark_safe(value.replace('\n', '&#92;&#92; \n'))


@register.filter(is_safe=False, needs_autoescape=True)
def safe_tex_url(value, autoescape=True):
    """
    Convert all newlines in a piece of plain text to HTML line breaks
    """
    return mark_safe(value.replace('#', '&#92;#'))
