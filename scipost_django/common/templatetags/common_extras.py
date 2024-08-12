__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def action_url(context, **extra_kwargs):
    kwargs = context["action_url_base_kwargs"]
    kwargs.update(extra_kwargs)
    return reverse(context["action_url_name"], kwargs=kwargs)


@register.filter
def replace(text, args):
    if len(args.split("|")) != 2:
        return text
    a, b = args.split("|")
    return text.replace(a, b)


@register.filter
def rstrip_minutes(text):
    if "day" in text or "hour" in text:
        return re.split("[0-9]+\xa0minutes", text, 1)[0].rstrip(", ")
    return text


@register.simple_tag
def equal(a, b):
    return a == b


# Math
@register.filter
def int_divide(a, b):
    return a // b


@register.filter
def multiply(a, b):
    return a * b

@register.filter
def index(list, index):
    return list[index]

@register.filter
def zip_dj(list1, list2):
    return zip(list1, list2)

# HTML
@register.filter
def article_safe(text):
    """
    Allow only a subset of HTML tags used in article content and escape the rest.
    Those tags are:
    - Hyperlinks <a>
    - Layout <span> <div> <hr> <br>
    - Semantics <article> <section> <header> <footer> <address>
    - Headings <h1>, <h2>, <h3>, <h4>, <h5>, <h6> <hgroup>
    - Text <p> <b>, <strong>, <i>, <em>, <u>, <s>, <strike>, <del>, <sup>, <sub>
    - Lists <ul>, <ol>, <li>
    - Referencing <blockquote> <cite> <pre> <code>
    - Images <img> (with src, alt, width, height)
    - Tables <table>, <tr>, <td>, <th>
    """
    # fmt: off
    allowed_tags = [
        "a", "span", "div", "hr", "br",
        "article", "section", "header", "footer", "address",
        "h1", "h2", "h3", "h4", "h5", "h6", "hgroup",
        "p", "b", "strong", "i", "em", "u", "s", "strike", "del", "sup", "sub",
        "ul", "ol", "li",
        "blockquote", "cite", "pre", "code",
        "img",
        "table", "tr", "td", "th",
    ]
    # fmt: on

    # Allow only the tags in the list above
    # text = re.sub(r"<(?!(?:%s)\b)([^>]*)>" % "|".join(allowed_tags), "", text)
    all_tags = re.findall(r"</?([^>]*)>", text)
    for tag in all_tags:
        if tag.split(" ")[0] not in allowed_tags:
            text = text.replace(f"<{tag}>", f"&lt;{tag}&gt;")
            text = text.replace(f"</{tag}>", f"&lt;/{tag}&gt;")

    return mark_safe(text)
