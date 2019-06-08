__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re


def detect_markup_language(text):
    """
    Detect which markup language is being used.

    This method returns a dictionary containing:

    * language
    * errors

    where ``language`` can be one of: plain, reStructuredText, Markdown

    The criteria used are:

    * if the ``math`` role or directive is found together with $...$, return error
    * if the ``math`` role or directive is found, return ReST

    Assumptions:

    * MathJax is set up with $...$ for inline, \[...\] for online equations.
    """

    # Inline maths
    inline_math = re.search("\$[^$]+\$", text)
    # if inline_math:
    #     print('inline math: %s' % inline_math.group(0))

    # Online maths is of the form \[ ... \]
    # The re.DOTALL is to also capture newline chars with the . (any single character)
    online_math = re.search(r'[\\][[].+[\\][\]]', text, re.DOTALL)
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
