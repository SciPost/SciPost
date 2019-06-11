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
    """Return first match object of regex search for inline maths $...$ or \(...\)."""
    match = re.search(r'\$[^$]+\$', text)
    if match:
        return match
    return re.search(r'\\\(.+\\\)', text)

def match_displayed_math(text):
    """Return first match object of regex search for displayed maths $$...$$ or \[...\]."""
    match = re.search(r'\$\$.+\$\$', text, re.DOTALL)
    if match:
        return match
    return re.search(r'\\\[.+\\\]', text, re.DOTALL)


# Markdown
def match_md_header(text, level=None):
    """
    Return first match object of regex search for Markdown headers in form #{level,}.

    If not level is given, all levels 1 to 6 are checked, returning the first match or None.
    """
    if not level:
        for newlevel in range(1,7):
            match = match_md_header(text, newlevel)
            if match:
                return match
        return None
    if not isinstance(level, int):
        raise TypeError('level must be an int')
    if level < 1 or level > 6:
        raise ValueError('level must be an integer from 1 to 6')
    return re.search(r'^#{' + str(level) + ',}[ ].+$', text)

def match_md_blockquote(text):
    """Return first match of regex search for Markdown blockquote."""
    return re.search(r'(^[ ]*>[ ].+){1,5}', text, re.DOTALL | re.MULTILINE)


# reStructuredText
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
        return none
    if directive not in ReST_DIRECTIVES:
        raise ValueError('this directive is not listed in ReST directives')
    print('regex = %s' % r'^\.\. ' + directive + '::(.+)*(\n(.+)*){1,3}')
    return re.search(r'^\.\. ' + directive + '::(.+)*(\n(.+)*){1,3}', text, re.MULTILINE)

def match_rst_header(text, symbol):
    """
    Return first match object of regex search for reStructuredText header.

    Python conventions are followed, namely that ``#`` and ``*`` headers have
    both over and underline (of equal length, so faulty ones are not matched),
    while the others (``=``, ``-``, ``"`` and ``^``) only have the underline.
    """
    if symbol not in ReST_HEADER_REGEX_DICT.keys():
        raise ValueError('symbol is not a ReST header symbol')
    return re.search(ReST_HEADER_REGEX_DICT[symbol], text, re.MULTILINE)


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

    The criteria used for error reporting are:

    * if the ``math`` role or directive is found together with inline/displayed maths
    """

    # Start from the default assumption
    detector = {
        'language': 'plain',
        'errors': None
    }

    # Inline maths is of the form $ ... $ or \( ... \)
    inline_math = match_inline_math(text)

    # Displayed maths is of the form \[ ... \] or $$ ... $$
    displayed_math = match_displayed_math(text)

    rst_math_role = match_rst_role(text, 'math')
    rst_math_directive = match_rst_directive(text, 'math')

    md_header = match_md_header(text)
    md_blockquote = match_md_blockquote(text)

    if rst_math_role or rst_math_directive:
        # reStructuredText presumed; check for errors
        if inline_math:
            detector['errors'] = (
                'You have mixed inline maths ($ ... $ or \( ... \) ) with '
                'reStructuredText markup.\n\nPlease use one or the other, but not both!')
            return detector
        elif displayed_math:
            detector['errors'] = (
                'You have mixed displayed maths ($$ ... $$ or \[ ... \]) with '
                'reStructuredText markup.\n\nPlease use one or the other, but not both!')
            return detector
        elif md_header:
            detector['errors'] = (
                'You have mixed Markdown headers with reStructuredText math roles/directives.'
                '\n\nPlease use one language only.')
        elif md_blockquote:
            detector['errors'] = (
                'You have mixed Markdown blockquotes with reStructuredText math roles/directives.'
                '\n\nPlease use one language only.')
        else:
            detector['language'] = 'reStructuredText'

    elif md_header or md_blockquote:
        detector['language'] = 'Markdown'

    return detector



def detect_markup_language_old(text):
    # Inline maths
    inline_math = match_inline_math(text)
    # if inline_math:
    #     print('inline math: %s' % inline_math.group(0))

    # Online maths is of the form \[ ... \]
    # The re.DOTALL is to also capture newline chars with the . (any single character)
    online_math = match_displayed_math(text)
    # if online_math:
    #     print('online math: %s' % online_math.group(0))

    rst_math = '.. math::' in text or ':math:`' in text

    # Detect Markdown:
    # Headlines: one or more # at the beginning of a line, space, then nonempty
    md_header_patterns = ["^#{1,}[ ].+$",]
    nr_md_headers = 0
    for header_pattern in md_header_patterns:
        matches = re.findall(header_pattern, text, flags=re.DOTALL)
        print ('Markdown: %s matched %d times' % (header_pattern, len(matches)))
        nr_md_headers += len(matches)
    if nr_md_headers > 0:
        return {
            'language': 'Markdown',
            'errors': None
            }

    # Normal inline/online maths cannot be used simultaneously with ReST math.
    # If this is detected, language is set to plain, and errors are reported.
    # Otherwise if math present in ReST but not in/online math, assume ReST.
    if rst_math:
        if inline_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n\n'
                           'You have mixed inline maths ($...$) with reStructuredText markup.'
                           '\n\nPlease use one or the other, but not both!')
            }
        elif online_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n\n'
                           'You have mixed online maths (\[...\]) with reStructuredText markup.'
                           '\n\nPlease use one or the other, but not both!')
            }
        else: # assume ReST
            return {
                'language': 'reStructuredText',
                'errors': None
            }

    # reStructuredText header patterns
    rst_header_patterns = [
        "^#{2,}$", "^\*{2,}$", "^={2,}$", "^-{2,}$", "^\^{2,}$", "^\"{2,}$",]
    # See list of reStructuredText directives at
    # http://docutils.sourceforge.net/0.4/docs/ref/rst/directives.html
    # We don't include the math one here since we covered it above.
    rst_directives = [
        "attention", "caution", "danger", "error", "hint", "important", "note", "tip",
        "warning", "admonition",
        "topic", "sidebar", "parsed-literal", "rubric", "epigraph", "highlights",
        "pull-quote", "compound", "container",
        "table", "csv-table", "list-table",
        "contents", "sectnum", "section-autonumbering", "header", "footer",
        "target-notes",
        "replace", "unicode", "date", "class", "role", "default-role",
    ]
    # See list at http://docutils.sourceforge.net/0.4/docs/ref/rst/roles.html
    rst_roles = [
        "emphasis", "literal", "pep-reference", "rfc-reference",
        "strong", "subscript", "superscript", "title-reference",
    ]

    nr_rst_headers = 0
    for header_pattern in rst_header_patterns:
        matches = re.findall(header_pattern, text, re.MULTILINE)
        print ('%s matched %d times' % (header_pattern, len(matches)))
        nr_rst_headers += len(matches)

    nr_rst_directives = 0
    for directive in rst_directives:
        if ('.. %s::' % directive) in text:
            nr_rst_directives += 1

    nr_rst_roles = 0
    for role in rst_roles:
        if (':%s:`' % role) in text:
            nr_rst_roles += 1

    if (nr_rst_headers > 0 or nr_rst_directives > 0 or nr_rst_roles > 0):
        if inline_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n\n'
                           'You have mixed inline maths ($...$) with reStructuredText markup.'
                           '\n\nPlease use one or the other, but not both!')
            }
        elif online_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n\n'
                           'You have mixed online maths (\[...\]) with reStructuredText markup.'
                           '\n\nPlease use one or the other, but not both!')
            }
        else:
            return {
                'language': 'reStructuredText',
                'errors': None
            }
    return {
        'language': 'plain',
        'errors': None
    }



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
