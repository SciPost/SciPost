import requests
from nameparser import HumanName

from .utils import QueryFragment, format_person_name, Person
from .server import BasePreprintServer, PreprintServer

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork


class FigshareServer(BasePreprintServer):
    name = "Figshare"
    api_url = "https://api.figshare.com/v2"
    base_url = "https://figshare.com"

    @classmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return f"https://doi.org/{identifier}"

    @classmethod
    def search(
        cls,
        text: str,
        domain: str = "articles",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        url = f"{cls.api_url}/{domain}/search"
        response = requests.post(url, json={"search_for": text, **kwargs})
        if not response.ok:
            return []

        return response.json()

    @classmethod
    def find_common_works_between(
        cls, *people: Person, **kwargs: dict[str, Any]
    ) -> list["CoauthoredWork"]:
        first_person, *other_people = people
        query = QueryFragment(":author: " + format_person_name(first_person))
        for person in other_people:
            query &= QueryFragment(":author: " + format_person_name(person))

        data = cls.search(str(query))
        return [parsed_work for item in data if (parsed_work := cls.parse_work(item))]

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        from ethics.models import CoauthoredWork

        def format_date(date_str: str | None) -> str | None:
            return date_str.split("T")[0] if date_str else None

        timeline = data.get("timeline", {})
        work = CoauthoredWork(
            server_source=PreprintServer.FIGSHARE.value,
            doi=data.get("doi", ""),
            title=data.get("title", ""),
            metadata=data,
        )
        work.authors = [HumanName(author) for author in data.get("authors", [])]
        work.date_published = format_date(
            timeline.get("publisherPublication")
        ) or format_date(data.get("published_date"))
        work.date_updated = format_date(timeline.get("revision"))

        return work
