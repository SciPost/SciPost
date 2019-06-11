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


def apply_markdown_preserving_displayed_maths_bracket(text):
    part = text.partition(r'\[')
    part2 = part[2].partition(r'\]')
    return '%s%s%s%s%s' % (
        markdown.markdown(part[0], output_format='html5'),
        part[1],
        part2[0],
        part2[1],
        apply_markdown_preserving_displayed_maths_bracket(part2[2]) if len(part2[2]) > 0 else '')

def apply_markdown_preserving_displayed_maths(text):
    """
    Processes the string text by first splitting out displayed maths, then applying
    Markdown on the non-displayed math parts.

    Both ``$$ ... $$`` and ``\[ ... \]`` are recognized, so a double recursive logic is used,
    first dealing with the ``$$ ... $$`` and then with the ``\[ .. \]``.
    See the complementary method ``apply_markdown_preserving_displayed_maths_bracket``.
    """
    part = text.partition('$$')
    part2 = part[2].partition('$$')
    return '%s%s%s%s%s' % (
        apply_markdown_preserving_displayed_maths_bracket(part[0]),
        part[1],
        part2[0],
        part2[1],
        apply_markdown_preserving_displayed_maths(part2[2]) if len(part2[2]) > 0 else '')


@register.filter(name='process_markup')
def process_markup(text, language_forced=None):
    if not text:
        return ''

    markup_detector = detect_markup_language(text)
    language = language_forced if language_forced else markup_detector['language']

    if markup_detector['errors']:
        return markup_detector['errors']

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
                apply_markdown_preserving_displayed_maths(text),
                tags=BLEACH_ALLOWED_TAGS
            )
        )

    else:
        return linebreaksbr(text)
