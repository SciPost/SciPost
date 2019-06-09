__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Dictionary for regex expressions to recognize reStructuredText headers.
# This follows the Python conventions: order is #, *, =, -, ", ^ and
# for the first two levels (# and *), over- and underlining are necessary, while
# only underlining is needed for the lower four levels.
# The regex search should use the re.MULTILINE flag.
ReST_HEADER_REGEX_DICT = {
    '#': r'^(#{1,}\n).+\n\1', # this makes use of a regex backreference
    '*': r'^(\*{1,}\n).+\n\1', # this makes use of a regex backreference
    '=': r'^={1,}\n',
    '-': r'^-{1,}\n',
    '"': r'^"{1,}\n',
    '^': r'^\^{1,}\n'
}

# See list at http://docutils.sourceforge.net/0.4/docs/ref/rst/roles.html
ReST_ROLES = [
    "math",
    "emphasis", "literal", "pep-reference", "rfc-reference",
    "strong", "subscript", "superscript", "title-reference"
]

# See list of reStructuredText directives at
# http://docutils.sourceforge.net/0.4/docs/ref/rst/directives.html
ReST_DIRECTIVES = [
    "math",
    "attention", "caution", "danger", "error", "hint", "important", "note", "tip",
    "warning", "admonition",
    "topic", "sidebar", "parsed-literal", "rubric", "epigraph", "highlights",
    "pull-quote", "compound", "container",
    "table", "csv-table", "list-table",
    "contents", "sectnum", "section-autonumbering", "header", "footer",
    "target-notes",
    "replace", "unicode", "date", "class", "role", "default-role"
]

BLEACH_ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'li', 'ol',
    'p', 'pre', 'strong', 'table', 'td', 'th', 'tr', 'ul',
]


MathSnippets = (
    {
        'title': 'Inline and online equations',
        'raw':
r"""Some say $e^{i\pi} + 1 = 0$ is the most beautiful equation there is.

Simple multiplication: $a * b = c$ and $a < b$ and $c < d$.

Ampersands: & and &amp; are both ampersands. Lesser than: &lt; is <
and $<$ is OK. What about AT&T?

Do you know this famous Hamiltonian?
\[
H = \sum_j {\boldsymbol S}_j \cdot {\boldsymbol S}_{j+1}
\]

What about this one?
$$
H = \int dx \left[ \partial_x \Psi^\dagger \partial_x \Psi
+ c \Psi^\dagger \Psi^\dagger \Psi \Psi \right]
$$
""",
    },
    {
        'title': 'Multiline equations',
        'raw':
r"""
<script>alert("Gotcha!");</script>

Maxwell's equations:

\[
\begin{align*}
\nabla \cdot {\boldsymbol E} &= \frac{\rho}{\epsilon_0}, &
\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t} &= 0, \\
\nabla \cdot {\boldsymbol B} &= 0, &
\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
&= \mu_0 {\boldsymbol J}
\end{align*}
\]

$$
\begin{align*}
\nabla \cdot {\boldsymbol E} &= \frac{\rho}{\epsilon_0}, &
\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t} &= 0, \\
\nabla \cdot {\boldsymbol B} &= 0, &
\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
&= \mu_0 {\boldsymbol J}
\end{align*}
$$

$$
\nabla \cdot {\boldsymbol E} = \frac{\rho}{\epsilon_0},
\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t} = 0, \\
\nabla \cdot {\boldsymbol B} = 0,
\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
= \mu_0 {\boldsymbol J}
\label{eq:Maxwell}
$$
"""
        },
)


PlainTextSnippets = {
    'maths_inline_online':
r"""Some say $e^{i\pi} + 1 = 0$ is the most beautiful equation of all.

Do you know this famous Hamiltonian?
\[
H = \sum_j {\boldsymbol S}_j \cdot {\boldsymbol S}_{j+1}
\]

What about this one?
$$
H = \int dx \left[ \partial_x \Psi^\dagger \partial_x \Psi
+ c \Psi^\dagger \Psi^\dagger \Psi \Psi \right]
$$
""",

    'maths_multiple_lines':
"""
Equations on multiple lines:
\[
\nabla \cdot {\boldsymbol E} = \frac{\rho}{\epsilon_0}, \qquad
\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t}= 0 \\\\
\nabla \cdot {\boldsymbol B} = 0, \qquad
\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
= \mu_0 {\boldsymbol J}
\]

\[
\begin{eqnarray*}
\nabla \cdot {\boldsymbol E} &=& \frac{\rho}{\epsilon_0}, \qquad
\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t} &=& 0 \\\\
\nabla \cdot {\boldsymbol B} &=& 0, \qquad
\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
&=& \mu_0 {\boldsymbol J}
\end{eqnarray*}
\]
"""
}


MarkdownSnippets = {
    'paragraphs':
"""Including an empty line between two blocks of text separates those into

two different paragraphs.

Typing text on consecutive lines separated
by linebreaks
will merge the lines into one
paragraph.

However if you explicitly end a line with two spaces
then a linebreak will be forced.""",

    'headers':
"""# Level 1 (html h1)
Topmost headline

## Level 2 (h2)
two

### Level 3 (h3)
three

#### Level 4 (h4)
four

##### Level 5 (h5)
five

###### Level 6 (h6)
six, lowest level available.""",

    'emphasis':
"""You can obtain italics with *asterisks* or _single underscores_,
and boldface using **double asterisks** or __double underscores__.

If you need to explicitly use these characters (namely \* and \_),
you can escape them with a backslash.""",

    'blockquotes':
"""> This is a blockquote with two paragraphs. You should begin
> each line with a ">" (greater than) symbol.
>
> Here is the second paragraph. The same wrapup rules
> apply as per
> normal paragraphs.

A line of normal text will separate blockquotes.

> Otherwise

> multiple blockquotes

> will be merged into one.

You can be lazy and simply put a single ">" in front of
a hard-wrapped paragraph, and all the
text will be included in a single wrapped-up blockquote.

> This is especially handy if you are copy and pasting e.g.
a referee's comment which you want to respond to, and
which spans
multiple
lines.

Finally,

> you can
>> nest
>>> many levels
>>>> of blockquotes

>>> and come back to a lower level by putting a blank line

>> to indicate a "terminated" level.
""",

    'lists':
"""Markdown supports unordered (bulleted) and ordered (numbered) lists.

Unordered list items are marked with asterisk, plus or hyphen, which
can be used interchangeable (even within a single list):

* first item
+ second item
- third item

Ordered list items are marked by a number (it does not matter which,
they will be automatically recomputed anyway) followed by a period:

1. first item
7. second item
123. third item
42. fourth item
1. fifth item

If you separate list items by blank lines, an HTML paragraph will
be wrapped around each item, giving more padding around the items:

1. first item

1. second item

Nested lists can be obtained by four-space (or tab) indentation:

1. First mainlist item
    1. first sublist item
    1. second sublist item
1. Second mainlist item""",

    'code':
"""An inline code span, to mention simple things like the
`print()` function, is obtained by wrapping it with single backticks.

A code block is obtained by indenting the code by 4 spaces or a tab:

    from django import forms

    class MarkupTextForm(forms.Form):
        markup_text = forms.CharField()

        def get_processed_markup(self):
            text = self.cleaned_data['markup_text']""",

    'hr':
"""A horizontal rule (HTML hr) can be obtained by writing three or
more asterisks, hyphens or underscores on a line by themselves:

text

***

more text

-----

more text
_______

Be careful to include an empty line before hyphens,
otherwise the system might

confuse the preceding text for a headline
-------
""",

    'links':
"""### Inline-style hyperlinks

Here is an example of an inline link to the [SciPost homepage](https://scipost.org/).

For example, one can also link to
a specific [Submission](https://scipost.org/submissions/1509.04230v5/)
or a specific [Report](https://scipost.org/submissions/1509.04230v4/#report_2).

### Reference-style hyperlinks

You can also use reference-style links when citing this [resource][md],
which you need to cite [again][md] and [again][md]
and [again][md].

The reference will be resolved provided you define the link label somewhere
in your text.

[md]: https://daringfireball.net/projects/markdown/syntax""",

    'maths_inline_online':
r"""### Inline maths

You can have simple inline equations like this: $E = mc^2$ by enclosing them with
dollar signs.

### Online maths

For online maths, you need to enclose the equations with double dollar signs:

$$
H = \sum_j S^x_j S^x_{j+1} + S^y_j S^y_{j+1} + \Delta S^z_j S^z_{j+1}
$$
"""
}


ReStructuredTextSnippets = {
    'maths_inline_online':
r"""Inline maths
============

For inline equations, you must use the :code:`math` role, for example :math:`E = mc^2`.

On-line maths
=============

For on-line display of equations, the :code:`math` directive must be used:

.. math::
  H = \sum_j {\boldsymbol S}_j \cdot {\boldsymbol S}_{j+1}"""
}
