__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from re import Match
from typing import Literal
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as ET


class MathJaxInlineProcessor(InlineProcessor):
    """
    Defines a processor for MathJax, producing either inline or display math.

    Args:
        pattern (str): The regular expression pattern to match.
        tag (str): The tag to use for the math element.
        math_display (Literal["inline", "display"]): The display mode for the math.
    """

    def __init__(self, pattern, math_display: Literal["inline", "display"]):
        super().__init__(pattern)
        self.math_display = math_display

    def handleMatch(self, match: Match, data):
        if "math" not in match.groupdict():
            return None, None, None

        if self.math_display == "display":
            el = ET.Element("div")
            el.text = "$$" + match.group("math") + "$$"
        elif self.math_display == "inline":
            el = ET.Element("span")
            el.text = "$" + match.group("math") + "$"
        else:
            raise ValueError(f"Invalid math display mode: {self.math_display}")

        return el, match.start(0), match.end(0)


class MathJaxExtension(Extension):
    """
    Defines a Markdown extension for MathJax, adding inline and display math.
    """

    # Define list of pairs of symbols to define the endpoints of math expressions.
    DISPLAY_SYMBOLS = [
        (r"\\\[", r"\\\]"),
        (r"\$\$", r"\$\$"),
    ]

    # Use negative lookbehind and lookahead to avoid matching $$
    INLINE_SYMBOLS = [
        (r"\\\(", r"\\\)"),
        (r"(?<!\$)\$(?!\$)", r"(?<!\$)\$(?!\$)"),
    ]

    def extendMarkdown(self, md):

        # Add inline math processors.
        for i, (start, end) in enumerate(self.INLINE_SYMBOLS):
            md.inlinePatterns.register(
                MathJaxInlineProcessor(
                    start + r"(?P<math>.+?)" + end, math_display="inline"
                ),
                "mathjax-inline-{i}",
                185 + i,
            )

        # Add display math processors.
        for i, (start, end) in enumerate(self.DISPLAY_SYMBOLS):
            md.inlinePatterns.register(
                MathJaxInlineProcessor(
                    start + r"(?P<math>.+?)" + end, math_display="display"
                ),
                f"mathjax-display-{i}",
                181 + i,
            )
