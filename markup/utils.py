__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import bleach
from docutils.core import publish_parts
import markdown
from io import StringIO
import re

from django.template.defaultfilters import linebreaksbr
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from .constants import ReST_HEADER_REGEX_DICT, ReST_ROLES, ReST_DIRECTIVES, BLEACH_ALLOWED_TAGS


# Inline or displayed math
def match_inline_math(text):
    """Return first match object of regex search for inline math ``$...$`` or ``\(...\)``."""
    match = re.search(r'\$[^$]+\$', text)
    if match:
        return match
    return re.search(r'\\\(.+\\\)', text)

def match_displayed_math(text):
    """Return first match object of regex search for displayed math ``$$...$$`` or ``\[...\]``."""
    match = re.search(r'\$\$.+\$\$', text, re.DOTALL)
    if match:
        return match
    return re.search(r'\\\[.+\\\]', text, re.DOTALL)


# Headers
def match_md_header(text, level=None):
    """
    Return first match object of regex search for Markdown headers in form #{level,}.

    If not level is given, all levels 1 to 6 are checked, returning the first match or None.
    """
    if not level:
        for newlevel in range(1, 7):
            match = match_md_header(text, newlevel)
            if match:
                return match
        return None
    if not isinstance(level, int):
        raise TypeError('level must be an int')
    if level < 1 or level > 6:
        raise ValueError('level must be an integer from 1 to 6')
    return re.search(r'^#{' + str(level) + ',}[ ].+$', text, re.MULTILINE)

def match_rst_header(text, symbol=None):
    """
    Return first match object of regex search for reStructuredText header.

    Python conventions are followed, namely that ``#`` and ``*`` headers have
    both over and underline (of equal length, so faulty ones are not matched),
    while the others (``=``, ``-``, ``"`` and ``^``) only have the underline.
    """
    if not symbol:
        for newsymbol in ['#', '*', '=', '-', '"', '^']: # explicit checking order
            match = match_rst_header(text, newsymbol)
            if match:
                return match
        return None
    if symbol not in ReST_HEADER_REGEX_DICT.keys():
        raise ValueError('symbol is not a ReST header symbol')
    return re.search(ReST_HEADER_REGEX_DICT[symbol], text, re.MULTILINE)


# Blockquotes
def match_md_blockquote(text):
    """Return first match of regex search for Markdown blockquote."""
    return re.search(r'(^[ ]*>[ ].+){1,5}', text, re.DOTALL | re.MULTILINE)


# Hyperlinks
def match_md_hyperlink_inline(text):
    """Return first match of regex search for Markdown inline hyperlink."""
    return re.search(r'\[.+\]\(http.+\)', text)

def match_md_hyperlink_reference(text):
    """Return first match of regex search for Markdown reference-style hyperlink."""
    return re.search(r'\[.+\]: http.+', text)

def match_rst_hyperlink_inline(text):
    """Return first match of regex search for reStructuredText inline hyperlink."""
    return re.search(r'`.+<http.+>`_', text)

def match_rst_hyperlink_reference(text):
    """Return first match of regex search for reStructuredText reference-style hyperlink."""
    # The match must not start with `_ (end of previous hyperlink) or contain
    # a < (it's then assumed to be an inline hyperlink with <http...).
    return re.search(r'`[^_][^<]+`_', text)


# reStructuredText roles and directives
def match_rst_role(text, role=None):
    """
    Return first match object of regex search for given ReST role :role:`... .

    If no role is given, all roles in ReST_ROLES are tested one by one.
    """
    if not role:
        for newrole in ReST_ROLES:
            match = match_rst_role(text, newrole)
            if match:
                return match
        return None
    if role not in ReST_ROLES:
        raise ValueError('this role is not listed in ReST roles')
    return re.search(r':' + role + ':`.+`', text)

def match_rst_directive(text, directive=None):
    """
    Return first match object of regex search for given ReST directive.

    If no directive is given, all directives in ReST_DIRECTIVES are tested one by one.

    The first one to three lines after the directive statement are also captured.
    """
    if not directive:
        for newdirective in ReST_DIRECTIVES:
            match = match_rst_directive(text, newdirective)
            if match:
                return match
        return None
    if directive not in ReST_DIRECTIVES:
        raise ValueError('this directive is not listed in ReST directives')
    return re.search(r'^\.\. ' + directive + '::(.+)*(\n(.+)*){1,3}', text, re.MULTILINE)

# Lists
def match_md_unordered_list(text):
    """Return first match of Markdown list (excluding ReST-shared * pattern)."""
    return re.search(r'(^[\s]*[+-][ ].+$[\n]*){1,3}', text, re.MULTILINE)

def match_md_or_rst_unordered_list(text):
    """Return first match of Markdown/ReST unordered list using shared * marker."""
    return re.search(r'(^[\s]*[\*][ ].+$[\n]*){1,3}', text, re.MULTILINE)

def match_md_or_rst_ordered_list(text):
    """Return the first match of Markdown/ReST ordered list (using numbers)."""
    return re.search(r'(^[\s]*[0-9]+.[ ].+$[\n]*){1,3}', text, re.MULTILINE)

def match_rst_ordered_list(text):
    return re.search(r'(^[\s]*[#]\.[ ].+$[\n]*){1,3}', text, re.MULTILINE)


def check_markers(markers):
    """
    Checks the consistency of a markers dictionary. Returns a detector.
    """
    markers_cut = {}
    for key, val in markers.items():
        markers_cut[key] = {}
        for key2, val2 in val.items():
            if val2:
                markers_cut[key][key2] = val2

    if len(markers_cut['rst']) > 0:
        if len(markers_cut['md']) > 0:
            return {
                'language': 'plain',
                'errors': ('Inconsistency: Markdown and reStructuredText syntaxes are mixed:\n\n'
                           'Markdown: %s\n\nreStructuredText: %s' % (
                               markers_cut['md'].popitem(),
                               markers_cut['rst'].popitem()))
            }
        elif len(markers_cut['plain_or_md']) > 0:
            return {
                'language': 'plain',
                'errors': ('Inconsistency: plain/Markdown and reStructuredText '
                           'syntaxes are mixed:\n\n'
                           'Markdown: %s\n\nreStructuredText: %s' % (
                               markers_cut['plain_or_md'].popitem(),
                               markers_cut['rst'].popitem()))
            }
        return {
            'language': 'reStructuredText',
            'errors': None,
        }

    elif len(markers_cut['md']) > 0:
        return {
            'language': 'Markdown',
            'errors': None,
        }

    elif len(markers_cut['md_or_rst']) > 0: # markup, but indeterminate; assume Markdown
        return {
            'language': 'Markdown',
            'errors': None,
        }

    return {
        'language': 'plain',
        'errors': None,
    }


def detect_markup_language(text):
    """
    Detect whether text is plain text, Markdown or reStructuredText.

    This method returns a dictionary containing:
    * language
    * errors

    Inline and displayed maths are assumed enabled through MathJax.
    For plain text and Markdown, this assumes the conventions
    * inline: $ ... $ and \( ... \)
    * displayed: $$ ... $$ and \[ ... \]

    while for reStructuredText, the ``math`` role and directive are used.

    We define markers, and indicator. A marker is a regex which occurs
    in only one of the languages. An indicator occurs in more than one,
    but not all languages.

    Language markers:

    Markdown:
    * headers: [one or more #] [non-empty text]
    * blockquotes: one or more lines starting with > [non-empty text]

    reStructuredText:
    * use of the :math: role or .. math: directive
    * [two or more #][blank space][carriage return]
      [text on a single line, as long as or shorter than # sequence]
      [same length of #]
    * same thing but for * headlines
    * other header markers (=, -, \" and \^)
    * use of any other role
    * use of any other directive

    Language indicators:

    Plain text or Markdown:
    * inline or displayed maths

    Markdown or reStructuredText:
    * [=]+ alone on a line  <- users discouraged to use this in Markdown
    * [-]+ alone on a line  <- users discouraged to use this in Markdown

    Exclusions (sources of errors):
    * inline or displayed maths cannot be used in ReST

    Any simultaneously present markers to two different languages
    return an error.

    Checking order:
    * maths
    * headers/blockquotes
    * hyperlinks
    * rst roles
    * rst directives
    """
    if not text:
        return {
            'language': 'plain',
            'errors': None,
        }

    markers = {
        'plain_or_md': {},
        'md': {},
        'md_or_rst': {},
        'rst': {},
    }

    # Maths
    # Inline maths is of the form $ ... $ or \( ... \)
    markers['plain_or_md']['inline_math'] = match_inline_math(text)
    # Displayed maths is of the form \[ ... \] or $$ ... $$
    markers['plain_or_md']['displayed_math'] = match_displayed_math(text)
    # For rst, check math role and directive
    markers['rst']['math_role'] = match_rst_role(text, 'math')
    markers['rst']['math_directive'] = match_rst_directive(text, 'math')

    # Headers and blockquotes
    markers['md']['header'] = match_md_header(text)
    markers['md']['blockquote'] = match_md_blockquote(text)
    markers['rst']['header'] = match_rst_header(text)

    # Lists
    markers['md']['unordered_list'] = match_md_unordered_list(text)
    markers['md_or_rst']['unordered_list'] = match_md_or_rst_unordered_list(text)
    markers['md_or_rst']['ordered_list'] = match_md_or_rst_ordered_list(text)
    markers['rst']['ordered_list'] = match_rst_ordered_list(text)

    # Hyperrefs
    markers['md']['href_inline'] = match_md_hyperlink_inline(text)
    markers['md']['href_reference'] = match_md_hyperlink_reference(text)
    markers['rst']['href_inline'] = match_rst_hyperlink_inline(text)
    markers['rst']['href_reference'] = match_rst_hyperlink_reference(text)

    # ReST roles and directives
    markers['rst']['role'] = match_rst_role(text)
    markers['rst']['directive'] = match_rst_directive(text)

    detector = check_markers(markers)
    return detector


def apply_markdown_preserving_displayed_maths_bracket(text):
    """
    Subsidiary function called by ``apply_markdown_preserving_displayed_maths``.
    See explanations in docstring of that method.
    """
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


def process_markup(text, language_forced=None):

    markup_detector = detect_markup_language(text)

    markup = {
        'language': 'plain',
        'errors': None,
        'warnings': None,
        'processed': ''
    }

    if language_forced and language_forced != markup_detector['language']:
        markup['warnings'] = (
            'Warning: markup language was forced to %s, while the detected one was %s.'
            ) % (language_forced, markup_detector['language'])

    language = language_forced if language_forced else markup_detector['language']
    markup['language'] = language
    markup['errors'] = markup_detector['errors']

    if markup['errors']:
        return markup

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
            markup['processed'] = mark_safe(force_text(parts['html_body']))
        except:
            markup['errors'] = warnStream.getvalue()

    elif language == 'Markdown':
        markup['processed'] = mark_safe(
            bleach.clean(
                apply_markdown_preserving_displayed_maths(text),
                tags=BLEACH_ALLOWED_TAGS
            )
        )

    else:
        markup['processed'] = linebreaksbr(text)

    return markup
