__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from functools import cached_property
import re
from typing import Any, Self

from nameparser import HumanName

from common.utils.text import latinise, partial_name_match_regexp
from conflicts.models import ConflictOfInterest
from .utils import (
    AUTHOR_FIRST_LAST_NAME_FORMAT,
    JSONResponse,
    Person,
    format_person_name,
)


class BaseQuery(ABC):
    @abstractmethod
    def query(self, text: str, **kwargs: Any) -> Self:
        pass


class BasePreprintServer(ABC):
    name: str
    base_url: str
    api_url: str
    query_type: type[BaseQuery]

    @classmethod
    @abstractmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return cls.base_url

    @classmethod
    @abstractmethod
    def search(cls, text: str, **kwargs: Any) -> JSONResponse:
        return cls.query(cls.query_type().query(text), **kwargs)

    @classmethod
    @abstractmethod
    def query(cls, query: BaseQuery) -> JSONResponse:
        pass

    @classmethod
    @abstractmethod
    def parse_work(cls, data: dict[str, Any]) -> "PreprintWork | None":
        pass


@dataclass
class PreprintWork:
    """
    A common representation of a preprint/submission/publication hosted in an external preprint server.
    Can be adapted to a SciPost Submission or a Coauthorship.
    """

    server: "PreprintServer"
    identifier: str
    title: str
    authors: list[HumanName]
    date_published: date | None
    date_updated: date | None
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    @property
    def url(self):
        if server_class := self.server.server_class:
            return server_class.identifier_to_url(self.identifier)

    def contains_authors(self, *people: Person) -> bool:
        """
        Return True if the author's last name is in the list of authors
        or if the entire name is in the list of authors if the last name
        cannot be separated
        """
        author_names = [
            format_person_name(author, format=AUTHOR_FIRST_LAST_NAME_FORMAT)
            for author in self.authors
        ]
        to_match_names = [
            format_person_name(person, format=AUTHOR_FIRST_LAST_NAME_FORMAT)
            for person in people
        ]

        total_matched = 0
        for match_name in to_match_names:
            match_regex = partial_name_match_regexp(latinise(match_name.lower()))
            pattern = re.compile(match_regex)
            for author_name in author_names:
                if pattern.match(latinise(author_name.lower())):
                    total_matched += 1
                    author_names.remove(author_name)
                    break

        return total_matched == len(people)

    def to_submission_form_prefill_data(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "date_published": self.date_published,
            "date_updated": self.date_updated,
            "metadata": self.metadata,
        }

    def to_coauthorship(self, **kwargs: Any) -> "Coauthorship":
        return ConflictOfInterest(
            **{
                "type": ConflictOfInterest.TYPE_COAUTHOR,
                "header": self.title,
                "url": self.url,
                "resource_date": self.date_published,
                **kwargs,
            }
        )

    def __repr__(self) -> str:
        return (
            f"<PreprintWork title={self.title}, "
            f"authors={'; '.join(format_person_name(author) for author in self.authors)}, "
            f"url={self.url}, date_published={self.date_published}>"
        )


class PreprintServer(Enum):
    CROSSREF = "crossref"
    ARXIV = "arxiv"
    CHEMARXIV = "chemrxiv"
    FIGSHARE = "figshare"
    OSF = "osf"

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def mapping() -> dict[str, type[BasePreprintServer]]:
        from . import (
            CrossrefServer,
            ArxivServer,
            ChemArxivServer,
            FigshareServer,
            OSFServer,
        )

        return {
            "crossref": CrossrefServer,
            "arxiv": ArxivServer,
            "chemrxiv": ChemArxivServer,
            "figshare": FigshareServer,
            "osf": OSFServer,
        }

    @property
    def server_class(self) -> type[BasePreprintServer] | None:
        return self.mapping().get(self.value)

    @classmethod
    def from_name(cls, name: str) -> "PreprintServer":
        for key, member in cls.__members__.items():
            if (
                key == name
                or member.value == name
                or getattr(member.server_class, "name", None) == name
            ):
                return member
        raise ValueError(f"Unknown preprint server: {name}")
