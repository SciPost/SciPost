import re
import feedparser
from datetime import datetime
from nameparser import HumanName

from django.utils.http import urlencode

from .utils import Person, format_person_name
from .server import BasePreprintServer, PreprintServer, PreprintWork

from typing import Any


class ArxivServer(BasePreprintServer):
    name = "arXiv"
    base_url = "https://arxiv.org"
    api_url = "http://export.arxiv.org/api"
    ID_REGEX = r"\d{4}\.\d{4,}(v\d+)?"

    @classmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return f"{cls.base_url}/abs/{identifier}"

    @classmethod
    def search(
        cls,
        text: str,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        id_list: list[str] = [],
        start: int = 0,
        max_results: int = 20,
        **kwargs: Any,
    ) -> feedparser.FeedParserDict:
        encoded_params = urlencode(
            {
                "search_query": text,
                "id_list": ",".join(id_list),
                "start": start,
                "sortBy": sort_by,
                "sortOrder": sort_order,
                "max_results": max_results,
            }
        )
        return feedparser.parse(f"{cls.api_url}/query?{encoded_params}")

    @classmethod
    def find_common_works_between(cls, *people: Person) -> list["PreprintWork"]:
        query = "au:" + ";".join([format_person_name(person) for person in people])
        results = cls.search(str(query))
        return [
            parsed_work
            for entry in results.entries
            if (parsed_work := cls.parse_work(entry))
        ]

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "PreprintWork | None":
        id_match = re.search(cls.ID_REGEX, data.get("link", ""))
        date_published = datetime.fromisoformat(data.get("published", "")).date()
        date_updated = datetime.fromisoformat(data.get("updated", "")).date()

        return PreprintWork(
            server=PreprintServer.ARXIV,
            identifier=id_match.group(0) if id_match else "",
            title=data.get("title", ""),
            authors=[HumanName(author.name) for author in data.get("authors", [])],
            date_published=date_published,
            date_updated=date_updated,
            metadata=data,
        )
