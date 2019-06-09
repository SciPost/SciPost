__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import bleach
from docutils.core import publish_parts
from io import StringIO
import markdown

from mdx_math import MathExtension

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

    language = language_forced if language_forced else markup_detector['language']

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
        # NB: bleach replaces & by &amp; and < by &lt;, and this breaks MathJax.
        # The solution is to force replace back, and then run markdown with
        # the mpx_math extension from python_markdown_math
        # (also allowing single-dollar delimiter for inline maths).
        # Users should be informed to NOT use < in maths without spaces around it:
        # $a<b$ is wrong (yields "$a" in output), whereas $a < b$ is fine (also standalone $<$).
        return mark_safe(
            markdown.markdown(
                bleach.clean(
                    text,
                    tags=BLEACH_ALLOWED_TAGS
                ).replace('&amp;', '&').replace(' &lt; ', ' < '),
                output_format='html5',
                extensions=[MathExtension(enable_dollar_delimiter=True)]
            )
        )
    else:
        return linebreaksbr(text)
