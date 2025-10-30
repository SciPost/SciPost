import requests
from nameparser import HumanName

from django.utils.http import urlencode
from django.utils.datastructures import MultiValueDict

from .server import BasePreprintServer, PreprintServer
from .utils import format_person_name, Person

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork


class ChemArxivQuery:
    def __init__(self):
        self._domain: str = "items"
        self.url_params = MultiValueDict[str, Any]()

    def query(self, text: str):
        self.url_params["term"] = text
        return self

    def author(self, author: str):
        """
        Uses specific author get param for authors.
        Will cause problems with initials.
        """
        self.url_params["author"] = author
        return self

    def order_by(self, key: str):
        ordering = "desc" if key.startswith("-") else "asc"
        self.url_params.update({"sort": (key.lstrip("-") + ordering).upper()})
        return self

    def __getitem__(self, s: slice):
        offset = s.start or 0
        self.url_params.update({"skip": offset, "limit": s.stop - offset})
        return self

    @property
    def url(self):
        url_params_lists_joined = {
            key: ",".join(url_param_values)
            for key, url_param_values in self.url_params.lists()
        }
        encoded_params = urlencode(url_params_lists_joined)
        return f"{self._domain}?{encoded_params}"


class ChemArxivServer(BasePreprintServer):
    name = "ChemArxiv"
    api_url = "https://chemrxiv.org/engage/chemrxiv/public-api/v1"
    base_url = "https://chemrxiv.org"
    query_type = ChemArxivQuery

    @classmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return f"https://doi.org/{identifier}"

    @classmethod
    def query(cls, query: ChemArxivQuery, **kwargs: Any) -> dict[str, Any]:
        response = requests.get(f"{cls.api_url}/{query.url}")
        if not response.ok:
            return {}
        return response.json()

    @classmethod
    def find_common_works_between(
        cls, *people: Person, **kwargs: Any
    ) -> list["CoauthoredWork"]:
        data = cls.query(
            ChemArxivQuery().author(
                " ".join([format_person_name(person) for person in people])
            )
        )
        items = [hit.get("item", {}) for hit in data.get("itemHits", [])]
        return [parsed_work for item in items if (parsed_work := cls.parse_work(item))]

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        from ethics.models import CoauthoredWork

        work = CoauthoredWork(
            server_source=PreprintServer.CHEMARXIV.value,
            work_type="preprint",
            doi=data.get("doi"),
            title=data.get("title", ""),
            date_published=data.get("publishedDate"),
            date_updated=data.get("statusDate"),
            metadata=data,
        )
        work.authors = [
            HumanName(last=author.get("lastName"), first=author.get("firstName"))
            for author in data.get("authors", [])
        ]
        return work
