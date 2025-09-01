import re
from nameparser import HumanName

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from profiles.models import Profile
    from scipost.models import Contributor
    from journals.models.publication import Publication
    from submissions.models.submission import Submission

Person = Union["Profile", "Contributor", "User", HumanName, str]
TitleHolder = Union["Submission", "Publication", str]
JSONResponse = Union[dict[str, Any], list[dict[str, Any]]]

AUTHOR_LAST_FIRST_NAME_FORMAT = "{last}, {first}"
AUTHOR_FIRST_LAST_NAME_FORMAT = "{first} {last}"


def isinstance_django_name(obj: Any, *names: str) -> bool:
    """
    Checks if the object's class name matches the given name.
    Usage: isinstance_django_name(obj, "Profile")
    """
    return type(obj).__name__ in names


class QueryFragment:
    def __init__(self, s: str):
        self.s = s

    def __and__(self, other: "QueryFragment") -> "QueryFragment":
        return QueryFragment(f"({self} AND {other})")

    def __or__(self, other: "QueryFragment") -> "QueryFragment":
        return QueryFragment(f"({self} OR {other})")

    def __invert__(self) -> "QueryFragment":
        return QueryFragment(f"NOT {self}")

    def __str__(self) -> str:
        return self.s

    def __repr__(self) -> str:
        return f"QueryFragment({self.s})"


def format_person_name(
    person: Person, format: str = AUTHOR_LAST_FIRST_NAME_FORMAT
) -> str:
    def fullstrip(s: str) -> str:
        return s.strip(" ,;")

    if isinstance(person, str):
        person = HumanName(person)
    if isinstance(person, HumanName):
        return fullstrip(format.format(**person.as_dict()))

    if isinstance_django_name(person, "Contributor"):
        try:
            person = person.profile
        except Contributor.profile.RelatedObjectDoesNotExist:
            person = person.user
    if isinstance_django_name(person, "User", "Profile"):
        return fullstrip(format.format(last=person.last_name, first=person.first_name))
    raise ValueError(f"Unsupported person type: {type(person)}")


def title_holder_to_title(holder: "TitleHolder") -> str:
    if isinstance_django_name(holder, "Submission", "Publication"):
        title = getattr(holder, "title", "")
    else:
        title = holder

    return title
