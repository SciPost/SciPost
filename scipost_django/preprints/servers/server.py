__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from abc import ABC, abstractmethod
from enum import Enum

from .utils import JSONResponse

from typing import Any, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork


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
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        pass


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
