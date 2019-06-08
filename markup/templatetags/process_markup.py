__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import bleach
from docutils.core import publish_parts
from io import StringIO
import markdown

from django import template
from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from ..constants import BLEACH_ALLOWED_TAGS
from ..utils import detect_markup_language


register = template.Library()


@register.filter(name='process_markup')
def process_markup(text, language_forced=None):
    if not text:
        return ''

    markup_detector = detect_markup_language(text)
    print('language detected: %s' % markup_detector['language'])

    if markup_detector['errors']:
        return markup_detector['errors']

    language = markup_detector['language']
    if language_forced:
        language = language_forced

    if language == 'reStructuredText':
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

    elif language == 'Markdown':
        return mark_safe(
            bleach.clean(
                markdown.markdown(text, output_format='html5'),
                tags=BLEACH_ALLOWED_TAGS)
        )
    else:
        return linebreaksbr(text)
