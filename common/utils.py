__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from datetime import timedelta
import re

from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template import loader

from .constants import CHARACTER_ALTERNATIVES


def alternative_spellings(text):
    """
    From a string, return a list with alternative spellings.

    Text searches can be run with accents stripped away.
    This is however insufficient if character sequences are interpreted
    as accented characters.

    This method provides a set of alternative spellings based on
    beyond-ignoring-accents substitutions.

    The substitutions which are handled are:
    - ae to/from ä (also capitalized)
    - oe to/from ö (also capitalized)
    - ue to/from ü (also capitalized)

    Limitations:
    - each substitution in the substitutions dictionary is applied to
      the whole of the text string (so this does not cover cases where
      a text string has inconsistent spelling mixing the different alternatives)
    """
    alternatives = set()
    for key, val in CHARACTER_ALTERNATIVES.items():
        alternatives.add(text.replace(key, val))
    return alternatives.difference((text,))


def Q_with_alternative_spellings(**lookup_dict):
    """
    Dress an existing Q query with alternative spellings.

    Keyword parameters:
    - lookup_dict: a single-entry dict giving the query

    Conditions:
    - lookup_dict contains a single entry
    - the to-be-match item must be of string type
    """
    if not len(lookup_dict) == 1:
        raise TypeError
    query = Q(**lookup_dict)
    query.connector = 'OR'
    lookup = query.children[0][0]
    text = query.children[0][1]
    if not isinstance(text, str):
        raise TypeError(text)
    alts = alternative_spellings(text)
    for alt in alts:
        query.children.append((lookup, alt))
    return query


def hslColorWheel(N=10, index=0, saturation=50, lightness=50):
    """
    Distributes colors into N values around a color wheel,
    according to hue-saturation-lightness (HSL).

    index takes values from 0 to N-1.
    """
    hue = int(index * 360/N % 360)
    saturation = max(saturation, 0)
    saturation = min(saturation, 100)
    lightness = max(lightness, 0)
    lightness = min(lightness, 100)

    return 'hsl(%s, %s%%, %s%%)' % (str(hue), str(saturation), str(lightness))


def workdays_between(datetime_from, datetime_until):
    """Return number of complete workdays.

    Given two datetime parameters, this function returns the
    number of complete workdays (defined as weekdays) separating them.
    """
    duration = datetime_until - datetime_from
    days = int(duration.total_seconds() // 86400)
    weeks = int(days // 7)
    daygenerator = (datetime_until - timedelta(x) for x in range(days - 7 * weeks))
    workdays = 5 * weeks + sum(1 for day in daygenerator if day.weekday() < 5)
    return workdays


class BaseMailUtil(object):
    mail_sender = 'no-reply@scipost.org'
    mail_sender_title = ''

    @classmethod
    def load(cls, _dict, request=None):
        cls._context = _dict
        cls._context['request'] = request
        for var_name in _dict:
            setattr(cls, var_name, _dict[var_name])

    def _send_mail(cls, template_name, recipients, subject, extra_bcc=None, extra_context={}):
        """
        Call this method from a classmethod to send emails.
        The template will have context variables defined appended from the `load` method.

        Arguments:
        template_name -- The .html template to use in the mail. The name be used to get the
                         following two templates:
                            `email/<template_name>.txt` (non-HTML)
                            `email/<template_name>.html`
        recipients -- List of mailaddresses to send to mail to.
        subject -- The subject of the mail.
        """
        template = loader.get_template('email/%s.txt' % template_name)
        html_template = loader.get_template('email/%s.html' % template_name)
        cls._context.update(extra_context)
        message = template.render(cls._context)
        html_message = html_template.render(cls._context)
        bcc_list = [cls.mail_sender]
        if extra_bcc:
            bcc_list += extra_bcc
        email = EmailMultiAlternatives(
            'SciPost: ' + subject,  # message,
            message,
            '%s <%s>' % (cls.mail_sender_title, cls.mail_sender),
            recipients,
            bcc=bcc_list,
            reply_to=[cls.mail_sender])
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)


def detect_markup_language(text):
    """
    Detect which markup language is being used.

    This method returns a dictionary containing:

    * language
    * errors

    Language can be one of: plain, reStructuredText

    The criteria used are:

    * if the ``math`` role or directive is found together with $...$, return error
    * if the ``math`` role or directive is found, return ReST

    Assumptions:

    * MathJax is set up with $...$ for inline, \[...\] for online equations.
    """

    # Inline maths
    inline_math = re.search("\$[^$]+\$", text)
    if inline_math:
        print('inline math: %s' % inline_math.group(0))
    # Online maths is of the form \[ ... \]
    # The re.DOTALL is to also capture newline chars with the . (any single character)
    online_math = re.search(r'[\\][[].+[\\][\]]', text, re.DOTALL)
    if online_math:
        print('online math: %s' % online_math.group(0))

    rst_math = '.. math::' in text or ':math:`' in text

    # Normal inline/online maths cannot be used simultaneously with ReST math.
    # If this is detected, language is set to plain, and errors are reported.
    # Otherwise if math present in ReST but not in/online math, assume ReST.
    if rst_math:
        if inline_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n'
                           'You have mixed inline maths ($...$) with reStructuredText markup.'
                           '\n\nPlease use one or the other, but not both!')
            }
        elif online_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n'
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
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n'
                           'You have mixed inline maths ($...$) with reStructuredText markup.'
                           '\n\nPlease use one or the other, but not both!')
            }
        elif online_math:
            return {
                'language': 'plain',
                'errors': ('Cannot determine whether this is plain text or reStructuredText.\n'
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
