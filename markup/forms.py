__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import bleach
from docutils.core import publish_parts
import markdown
import re

from mdx_math import MathExtension

from django import forms
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from .constants import BLEACH_ALLOWED_TAGS
from .utils import detect_markup_language


class MarkupTextForm(forms.Form):
    markup_text = forms.CharField()

    def get_processed_markup(self):
        text = self.cleaned_data['markup_text']

        # Detect text format
        markup_detector = detect_markup_language(text)
        language = markup_detector['language']

        if markup_detector['errors']:
            return markup_detector

        if language == 'reStructuredText':
            # This performs the same actions as the restructuredtext filter of app scipost
            from io import StringIO
            warnStream = StringIO()
            try:
                parts = publish_parts(
                    source=text,
                    writer_name='html5_polyglot',
                    settings_overrides={
                        'math_output': 'MathJax https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML,Safe',
                        'initial_header_level': 1,
                        'doctitle_xform': False,
                        'raw_enabled': False,
                        'file_insertion_enabled': False,
                        'warning_stream': warnStream
                    })
                return {
                    'language': language,
                    'processed_markup': mark_safe(force_text(parts['html_body'])),
                }
            except:
                pass
            return {
                'language': language,
                'errors': warnStream.getvalue()
            }

        elif language == 'Markdown':
            return {
                'language': language,
                'processed_markup': mark_safe(
                    markdown.markdown(
                        bleach.clean(
                            text,
                            tags=BLEACH_ALLOWED_TAGS
                        ).replace('&amp;', '&').replace(' &lt; ', ' < '),
                        output_format='html5',
                        extensions=[MathExtension(enable_dollar_delimiter=True)]
                    )
                )
            }

        # at this point, language is assumed to be plain text
        from django.template.defaultfilters import linebreaksbr
        return {
            'language': language,
            'processed_markup': linebreaksbr(text)
            }
