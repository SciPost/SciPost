__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from abc import ABC, abstractmethod
from enum import Enum
import time
import requests

from .utils import JSONResponse, Person

from typing import Any, Self, TYPE_CHECKING

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork


class BaseQuery(ABC):
    @abstractmethod
    def query(self, text: str, **kwargs: Any) -> Self:
        pass

    @property
    @abstractmethod
    def url(self) -> str: ...


class BasePreprintServer(ABC):
    name: str
    base_url: str
    api_url: str
    query_type: type[BaseQuery]

    MAX_REQUESTS_PER_SECOND: float | None = None
    _last_request_timestamp: float | None = None

    @classmethod
    @abstractmethod
    def identifier_to_url(cls, identifier: str) -> str: ...

    @classmethod
    def _limit_rate(cls) -> None:
        if cls.MAX_REQUESTS_PER_SECOND is None:
            return

        now = time.monotonic()
        if cls._last_request_timestamp is not None:
            elapsed = now - cls._last_request_timestamp
            wait_time = max(0, 1 / cls.MAX_REQUESTS_PER_SECOND - elapsed)
            time.sleep(wait_time)
        cls._last_request_timestamp = time.monotonic()

    @classmethod
    def request(cls, query: BaseQuery, **kwargs: Any) -> JSONResponse:
        cls._limit_rate()
        response = requests.get(f"{cls.api_url}/{query.url}")
        response.raise_for_status()
        return response.json()

    @classmethod
    def search(cls, text: str, **kwargs: Any) -> JSONResponse:
        constructed_query = cls.query_type().query(text, **kwargs)
        return cls.request(constructed_query, **kwargs)

    @classmethod
    @abstractmethod
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def find_common_works_between(
        cls, *people: Person, **kwargs: Any
    ) -> list["CoauthoredWork"]:
        raise NotImplementedError("Subclasses must implement this method")


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
    def server_class(self) -> type[BasePreprintServer]:
        return self.mapping()[self.value]

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
