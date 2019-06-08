__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from docutils.core import publish_parts
from io import StringIO
import markdown
from markupsafe import escape

from django import template
from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from ..utils import detect_markup_language

register = template.Library()


@register.filter(name='process_markup')
def process_markup(text):
    if not text:
        return ''

    markup_detector = detect_markup_language(text)

    if markup_detector['errors']:
        return markup_detector['errors']

    if markup_detector['language'] == 'reStructuredText':
        warnStream = StringIO()
        try:
            parts = publish_parts(
                source=text,
                writer_name='html5_polyglot',
                settings_overrides={
                    'math_output': 'MathJax  https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML,Safe',
                    'initial_header_level': 1,
                    'doctitle_xform': False,
                    'raw_enabled': False,
                    'file_insertion_enabled': False,
                    'warning_stream': warnStream
                })
            return mark_safe(force_text(parts['html_body']))
        except:
            return warnStream.getvalue()

    elif markup_detector['language'] == 'Markdown':
        return mark_safe(markdown.markdown(escape(text), output_format='html5'))

    else:
        return linebreaksbr(text)
