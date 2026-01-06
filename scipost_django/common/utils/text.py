__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import re

from django.db.models import Q

from ..constants import CHARACTER_ALTERNATIVES, CHARACTER_LATINISATIONS

import unicodedata


def initialize(name: str) -> str:
    """
    Convert a full name to its initials.
    """
    return " ".join([word.upper()[0] + "." for word in name.split()])


def unaccent(text: str) -> str:
    """
    Remove accented characters in the given string (e.g. é -> e),
    with the exception of the German umlauts (e.g. ö -> oe).
    """
    UMLAUT = "\u0308"

    unaccented_text = ""
    for char in unicodedata.normalize("NFD", text):
        char_category = unicodedata.category(char)

        if char_category != "Mn":
            unaccented_text += char
        elif char == UMLAUT:
            unaccented_text += "e"

    return unaccented_text


def latinise(text: str) -> str:
    """
    Convert accented characters in the given string to their
    latinised equivalents / lookalikes (e.g. ö -> o).
    """
    latinised_text = ""
    for char in unicodedata.normalize("NFD", text):
        char_category = unicodedata.category(char)

        translated_char = char
        is_latin = ord(char) < 128

        # Keep spaces and dashes
        if char in [" ", "-", "–"]:
            pass
        # Remove apostrophes and parentheses
        elif char in ["'", "’", "(", ")"]:
            translated_char = ""
        # Translate only letters, symbols and punctuation
        # skipping numbers and other characters (e.g. diacritics)
        elif char_category[0] in ["L", "S", "P"] and not is_latin:
            translated_char = CHARACTER_LATINISATIONS.get(char, "")

        # Remove everything not in the ASCII range
        translated_char = translated_char.encode("ascii", "ignore").decode("utf-8")

        latinised_text += translated_char

    # Remove multiple spaces
    latinised_text = " ".join(latinised_text.split())

    return latinised_text


def alternative_spellings(text):
    """
    From a string, return a list with alternative spellings.

    Text searches can be run with accents stripped away.
    This is however insufficient if character sequences are interpreted
    as accented characters.

    This method provides a set of alternative spellings based on
    beyond-ignoring-accents substitutions.

    The substitutions which are handled are:

    * ae to/from ä (also capitalized)
    * oe to/from ö (also capitalized)
    * ue to/from ü (also capitalized)

    Limitations:

    * each substitution in the substitutions dictionary is applied to
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
    query.connector = "OR"
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
    hue = int(index * 360 / N % 360)
    saturation = max(saturation, 0)
    saturation = min(saturation, 100)
    lightness = max(lightness, 0)
    lightness = min(lightness, 100)

    return "hsl(%s, %s%%, %s%%)" % (str(hue), str(saturation), str(lightness))


date_or_time = datetime.datetime | datetime.date


def workdays_between(date_from: date_or_time, date_until: date_or_time):
    """Return number of complete workdays.

    Given two datetime parameters, this function returns the
    number of complete workdays (defined as weekdays) separating them.
    """
    _from = date_from
    _until = date_until
    if isinstance(date_from, datetime.datetime):
        _from = date_from.date()
    if isinstance(date_until, datetime.datetime):
        _until = date_until.date()
    duration = _until - _from
    days = int(duration.total_seconds() // 86400)
    weeks = int(days // 7)
    daygenerator = (_until - datetime.timedelta(x) for x in range(days - 7 * weeks))
    workdays = 5 * weeks + sum(1 for day in daygenerator if day.weekday() < 5)
    return workdays


def shift_month(month: int, shift: int) -> int:
    """
    Return the ordinal of the month shifted by a given number of months.
    Months are numbered from 1 to 12.
    Negative shifts are allowed to go back in time.
    """
    return (month - 1 + shift) % 12 + 1


def jatsify_tags(text):
    """
    Adds the `jats:` prefix to basic HTML tags. Nilpotent.
    """
    tags = ["alternatives", "p", "inline-formula", "tex-math"]
    jatsified = text
    for tag in tags:
        jatsified = jatsified.replace(f"<{tag}>", f"<jats:{tag}>").replace(
            f"</{tag}>", f"</jats:{tag}>"
        )
    return jatsified


def remove_extra_spacing(text):
    """
    Remove extra spacing from text in the form of multiple spaces.
    """
    return " ".join(text.strip().split())


def split_strip(text: str, delimiter=",") -> list[str]:
    """
    Split a string by a delimiter and strip each part.
    """
    return [part.strip() for part in text.split(delimiter)]


def space_uppercase(text: str) -> str:
    """
    Space out uppercase characters in a string.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", " ", text)


def partial_name_match_regexp(name: str) -> str:
    """
    Return a regular expression to match a partial name with initials and separators.
    Example: "Rachel Anne-Marie" -> "^((Rachel|Anne|Marie|R|A|M)( -.)?)+$"
    """
    SEPARATORS = r"[ \-\.]"

    name_cleaned = re.sub(SEPARATORS, " ", name)
    name_parts = name_cleaned.split()
    name_initials = [part[0] for part in name_parts if len(part) > 1]

    name_parts_or_initials = name_parts + name_initials

    return "^(({names_ORed}){SEPARATORS}*)+$".format(
        names_ORed="|".join(name_parts_or_initials),
        SEPARATORS=SEPARATORS,
    )


def partial_names_match(partial: str, full: str, symmetric: bool = False) -> bool:
    """
    Check if a (partial) name matches another (full) name,
    via the partial name matching regular expression. partial ~=< full.
    If `symmetric` is True, it also matches for the reverse inputs (full ~=< partial).
    """
    match = re.match(partial_name_match_regexp(partial), full) is not None

    if symmetric:
        match |= re.match(partial_name_match_regexp(full), partial) is not None

    return match


def title_to_kebab(text: str) -> str:
    """
    Convert a title to a kebab-case string.
    """
    text = re.sub(r"([A-Z])", r"-\1", text).lower()
    text = text.lstrip("-")
    return text
