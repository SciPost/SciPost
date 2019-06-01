__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter(name='restructuredtext')
def restructuredtext(text):
    if not text:
        return ''
    from docutils.core import publish_parts
    parts = publish_parts(
        source=text,
        writer_name='html5_polyglot',
        settings_overrides={
            'math_output': 'MathJax  https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML,Safe',
                    'initial_header_level': 1,
                    'doctitle_xform': False
        })
    return mark_safe(force_text(parts['html_body']))
