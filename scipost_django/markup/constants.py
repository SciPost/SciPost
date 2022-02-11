__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Dictionary for regex expressions to recognize reStructuredText headers.
# This follows the Python conventions: order is #, *, =, -, ", ^ and
# for the first two levels (# and *), over- and underlining are necessary, while
# only underlining is needed for the lower four levels. In all cases we
# require the headline title to be at least one character long, and placed
# right above the lower headline marker.
# The regex search should use the re.MULTILINE flag.
ReST_HEADER_REGEX_DICT = {
    "#": r"^(#{1,}[^\S\n]*\n).{1,}\n\1",  # this makes use of a regex backreference
    "*": r"^(\*{1,}[^\S\n]*\n).{1,}\n\1",  # this makes use of a regex backreference
    "=": r"^.{1,}[^\S\n]*\n={1,}[^\S\n]*\n",  # non-empty line followed by line of =
    "-": r"^.{1,}[^\S\n]*\n-{1,}[^\S\n]*\n",  # non-empty line followed by line of -
    '"': r'^.{1,}[^\S\n]*\n"{1,}[^\S\n]*\n',  # non-empty line followed by line of "
    "^": r"^.{1,}[^\S\n]*\n\^{1,}[^\S\n]*\n",  # non-empty line followed by line of ^
}

# See list at http://docutils.sourceforge.net/0.4/docs/ref/rst/roles.html
ReST_ROLES = [
    "math",
    "emphasis",
    "literal",
    "pep-reference",
    "rfc-reference",
    "strong",
    "subscript",
    "superscript",
    "title-reference",
]

# See list of reStructuredText directives at
# http://docutils.sourceforge.net/0.4/docs/ref/rst/directives.html
ReST_DIRECTIVES = [
    "math",
    "attention",
    "caution",
    "danger",
    "error",
    "hint",
    "important",
    "note",
    "tip",
    "warning",
    "admonition",
    "topic",
    "sidebar",
    "parsed-literal",
    "rubric",
    "epigraph",
    "highlights",
    "pull-quote",
    "compound",
    "container",
    "table",
    "csv-table",
    "list-table",
    "contents",
    "sectnum",
    "section-autonumbering",
    "header",
    "footer",
    "target-notes",
    "replace",
    "unicode",
    "date",
    "class",
    "role",
    "default-role",
]

BLEACH_ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "td",
    "th",
    "tr",
    "ul",
]
BLEACH_ALLOWED_ATTRIBUTES = {
    "*": ["id"],
    "a": ["href", "rel"],
}

PlainTextSuggestedFormatting = (
    {
        "id": "authorreply",
        "title": "Author Reply to Report",
        "raw": r"""
The referee writes:
"The authors should extend their exact solution to the two-dimensional case."

Our response:
Even Bethe did not manage this: see the unfulfilled promise at the end
of his 1931 paper https://doi.org/10.1007/BF01341708.
""",
    },
)


PlainTextSnippets = (
    {
        "id": "maths",
        "title": "Maths: inline and displayed",
        "raw": r"""Some say $e^{i\pi} + 1 = 0$ is the most beautiful equation of all.

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
        "id": "maths_multiple_lines",
        "title": "Maths: multiple lines",
        "raw": r"""
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
""",
    },
)


MarkdownSuggestedFormatting = (
    {
        "id": "authorreply",
        "title": "Author Reply to Report",
        "raw": r"""
**The referee writes:**
> The authors should extend their exact solution to the two-dimensional case.

**Our response:**

Even Bethe did not manage this: see the unfulfilled promise at the end
of his [1931 paper](https://doi.org/10.1007/BF01341708).
""",
    },
)


MarkdownSnippets = (
    {
        "id": "paragraphs",
        "title": "Paragraphs and line breaks",
        "raw": """Including an empty line between two blocks of text separates those into

two different paragraphs.

Typing text on consecutive lines separated
by linebreaks
will merge the lines into one
paragraph.

However if you explicitly end a line with two spaces
then a linebreak will be forced.""",
    },
    {
        "id": "headlines",
        "title": "Headlines",
        "raw": """# Level 1 (html h1)
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
    },
    {
        "id": "emphasis",
        "title": "Emphasis",
        "raw": """You can obtain italics with *asterisks* or _single underscores_,
and boldface using **double asterisks** or __double underscores__.

If you need to explicitly use these characters (namely \* and \_),
you can escape them with a backslash.""",
    },
    {
        "id": "blockquotes",
        "title": "Blockquotes",
        "raw": """> This is a blockquote with two paragraphs. You should begin
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
    },
    {
        "id": "lists",
        "title": "Lists",
        "raw": """Markdown supports unordered (bulleted) and ordered (numbered) lists.

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
    },
    {
        "id": "code",
        "title": "Code",
        "raw": """An inline code span, to mention simple things like the
`print()` function, is obtained by wrapping it with single backticks.

A code block is obtained by indenting the code by 4 spaces or a tab:

    from django import forms

    class MarkupTextForm(forms.Form):
        markup_text = forms.CharField()

        def get_processed_markup(self):
            text = self.cleaned_data['markup_text']""",
    },
    {
        "id": "hr",
        "title": "Horizontal rules",
        "raw": """A horizontal rule (HTML hr) can be obtained by writing three or
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
    },
    {
        "id": "links",
        "title": "Links",
        "raw": """### Inline-style hyperlinks

Here is an example of an inline link to the [SciPost homepage](https://scipost.org/).
Please always use the full protocol in the URL
(so https://scipost.org instead of just scipost.org).

For example, one can also link to
a specific [Submission](https://scipost.org/submissions/1509.04230v5/) or
a specific [Report](https://scipost.org/submissions/1509.04230v4/#report_2).

### Reference-style hyperlinks

You can also use reference-style links when citing this [resource][md],
which you need to cite [again][md] and [again][md] and [again][md].

The reference will be resolved provided you define the link label somewhere in your text.

[md]: https://daringfireball.net/projects/markdown/syntax

### In-text hyperlinks

You can also give ids to elements, and then hyperlink to them. For example,
the headline

#### You haff to vork feery feeery haaaaart { #work-like-bethe }

can be linked to as follows:

[Work like Bethe](#work-like-bethe).
""",
    },
    {
        "id": "mathematics",
        "title": "Mathematics",
        "raw": r"""### Inline maths

You can have simple inline equations like this: $E = mc^2$ by enclosing them with
dollar signs.

### Displayed maths

For displayed maths, you need to enclose the equations with escaped square brackets

\[
H = \sum_j {\boldsymbol S}_j \cdot {\boldsymbol S}_{j+1}
\]

or with double dollar signs (though it works, this is less good,
since beginning and end markers are not distinguishable):

$$
H = \sum_j S^x_j S^x_{j+1} + S^y_j S^y_{j+1} + \Delta S^z_j S^z_{j+1}
$$

Multiline equations can be obtained by using the ``\\`` carriage return as usual;
to align your equations, use the ``align`` environment. For example:

\[
\begin{align*}
\nabla \cdot {\boldsymbol E} &= \frac{\rho}{\epsilon_0}, &
\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t} &= 0, \\
\nabla \cdot {\boldsymbol B} &= 0, &
\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
&= \mu_0 {\boldsymbol J}
\end{align*}
\]
""",
    },
)


ReStructuredTextSnippets = (
    {
        "id": "paragraphs",
        "title": "Paragraphs and line breaks",
        "raw": """Including an empty line between two blocks of text separates those into

two different paragraphs.

Typing text on consecutive lines separated
by linebreaks
will merge the lines into one
paragraph.

As in Python, indentation is significant, so lines of a paragraph have to be
indented to the same level.""",
    },
    {
        "id": "headlines",
        "title": "Headlines",
        "raw": """##################
Level 1 (html h1)
##################

Topmost headline

*****************
Level 2 (h2)
*****************

two

Level 3 (h3)
==================

three

Level 4 (h4)
-------------------

four

Level 5 (h5)
\"\"\"\"\"\"\"\"\"\"\"\"\"\"\"

five

Level 6 (h6)
^^^^^^^^^^^^^^^^^^^

six, lowest level available.""",
    },
    {
        "id": "emphasis",
        "title": "Emphasis",
        "raw": """You can obtain italics with *asterisks*,
boldface using **double asterisks** and code samples using ``double backquotes``.
Note that these cannot be nested, and that there must not be a space at the
start or end of the contents.

If you need to explicitly use these characters (namely \*),
you can escape them with a backslash.""",
    },
    {
        "id": "blockquotes",
        "title": "Blockquotes",
        "raw": """It is often handy to use blockquotes.

 This is a blockquote with two paragraphs, obtained by simple
 indentation from the surrounding text. For multiple lines,
 each line should be indented the same.

 Here is the second paragraph, with lines indented
 to the same level as the previous ones to preserve the
 blockquote.

To preserve line breaks, you can use line blocks:

| Here is
| a small paragraph
| with linebreaks preserved.

""",
    },
    {
        "id": "lists",
        "title": "Lists",
        "raw": """reStructuredText supports unordered (bulleted) and ordered (numbered) lists.

Unordered list items are marked with asterisk:

* first item
* second item
* third item

Ordered list items are marked by a number or # followed by a period:

1. first item
2. second item
3. third item


Nested lists can be obtained by indentation:

* First mainlist item

  * first sublist item
  * second sublist item
* Second mainlist item


There are also *definition lists* obtained like this:

term (up to a line of text)
   Definition of the term, which must be indented

   and can even consist of multiple paragraphs

next term
   Description.
""",
    },
    {
        "id": "code",
        "title": "Code",
        "raw": """An inline code span, to mention simple things like the
``print()`` function, is obtained by wrapping it with double backticks.

A code block is obtained by the ``::`` marker followed by the indented code::

    from django import forms

    class MarkupTextForm(forms.Form):
        markup_text = forms.CharField()

        def get_processed_markup(self):
            text = self.cleaned_data['markup_text']

which can then be followed by normal text.""",
    },
    {
        "id": "tables",
        "title": "Tables",
        "raw": """
A grid table can be written by "painting" it directly:

+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+

""",
    },
    {
        "id": "links",
        "title": "Links",
        "raw": """Here is an example of an inline link to the `SciPost homepage <https://scipost.org/>`_.

For example, one can also link to
a specific `Submission <https://scipost.org/submissions/1509.04230v5/>`_
or a specific `Report <https://scipost.org/submissions/1509.04230v4/#report_2>`_.

You can also use reference-style links when citing this `resource`_, the reference
will be resolved provided you define the link label somewhere
in your text.

.. _resource: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html""",
    },
    {
        "id": "mathematics",
        "title": "Mathematics",
        "raw": r"""
For simple inline equations, use the :code:`math` role like this: :math:`E = mc^2`.

For displayed maths, the :code:`math` directive must be used:

.. math::
  H = \sum_j {\boldsymbol S}_j \cdot {\boldsymbol S}_{j+1}

Multiline equations can be obtained by using the ``\\`` carriage return as usual:

.. math::
  &\nabla \cdot {\boldsymbol E} = \frac{\rho}{\epsilon_0},
  &\nabla \times {\boldsymbol E} + \frac{\partial \boldsymbol B}{\partial t} = 0, \\
  &\nabla \cdot {\boldsymbol B} = 0,
  &\nabla \times {\boldsymbol B} - \frac{1}{c^2} \frac{\partial \boldsymbol E}{\partial t}
  = \mu_0 {\boldsymbol J}

""",
    },
)


ReSTSuggestedFormatting = (
    {
        "id": "authorreply",
        "title": "Author Reply to Report",
        "raw": r"""
**The referee writes:**

  The authors should extend their exact solution to the two-dimensional case.

**Our response:**

Even Bethe did not manage this: see the unfulfilled promise at the end
of his `1931 paper <https://doi.org/10.1007/BF01341708>`_ .
""",
    },
)
