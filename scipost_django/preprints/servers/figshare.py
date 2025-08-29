import requests
from nameparser import HumanName

from .utils import QueryFragment, format_person_name, Person
from .server import BasePreprintServer, PreprintServer, PreprintWork

from typing import Any


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
    def find_common_works_between(cls, *people: Person) -> list["PreprintWork"]:
        first_person, *other_people = people
        query = QueryFragment(":author: " + format_person_name(first_person))
        for person in other_people:
            query &= QueryFragment(":author: " + format_person_name(person))

        data = cls.search(str(query))
        return [parsed_work for item in data if (parsed_work := cls.parse_work(item))]

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "PreprintWork | None":
        timeline = data.get("timeline", {})
        return PreprintWork(
            server=PreprintServer.FIGSHARE,
            identifier=data.get("doi", ""),
            title=data.get("title", ""),
            authors=[HumanName(author) for author in data.get("authors", [])],
            date_published=timeline.get("publisherPublication")
            or data.get("published_date"),
            date_updated=timeline.get("revision", None),
            metadata=data,
        )
