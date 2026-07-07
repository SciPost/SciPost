from datetime import date, datetime
from functools import reduce
from typing import TYPE_CHECKING, Any, override

import requests
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from nameparser import HumanName
from SciPost_v1.settings.base import SCIPOST_USER_AGENT

from .server import BasePreprintServer, BaseQuery, PreprintServer
from .utils import KeywordQueryFragment, Person, format_person_name

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork

class DataciteQuery(BaseQuery):
    def __init__(self) -> None:
        self._domain: str = "works"
        self.url_params = MultiValueDict[str, Any]()

    def domain(self, domain: str):
        self._domain = domain
        return self

    def query(self, **kwargs: str):
        for key, value in kwargs.items():
            key = key.replace("__", ".")
            self.url_params.appendlist("query", KeywordQueryFragment(key, value))
        return self

    def filter(self, **kwargs: str):
        for key, value in kwargs.items():
            kebab_key = key.replace("_", "-")
            self.url_params.appendlist(kebab_key, value)
        return self

    def select(self, *fields: str):
        self.url_params.update({f"fields[{self._domain}]": ",".join(fields)})
        return self

    def order_by(self, key: str = "relevance"):
        self.url_params.update({"sort": key})
        return self

    def include(self, **kwargs: bool):
        PERMITTED_INCLUDES = {"affiliation", "publisher", "detail"}
        for key in PERMITTED_INCLUDES:
            should_fetch = kwargs.pop(key, False)
            self.url_params.appendlist("include", {key: str(should_fetch).lower()})
        if kwargs:
            raise ValueError(
                f"Invalid include keys: {', '.join(kwargs.keys())}. Must be one of: {', '.join(PERMITTED_INCLUDES)}."
            )
        return self

    @property
    def url(self):
        if "query" in self.url_params:
            query_fragments = self.url_params.getlist("query")
            combined_query = reduce(lambda x, y: x & y, query_fragments)
            self.url_params.setlist("query", [str(combined_query)])

        if "include" not in self.url_params:
            self.include()

        if included_params := self.url_params.pop("include", None):
            for include_dict in included_params:
                for key, value in include_dict.items():
                    self.url_params.appendlist(key, value)

        if "sort" not in self.url_params:
            self.order_by()

        encoded_params = urlencode(self.url_params, doseq=True)
        return f"dois?{encoded_params}"


class DataciteServer(BasePreprintServer):
    name = "Datacite"
    base_url = "https://www.datacite.org"
    api_url = "https://api.datacite.org"
    query_type = DataciteQuery

    MAX_REQUESTS_PER_SECOND = 1 / 1.0

    @classmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return f"https://doi.org/{identifier}"

    @classmethod
    def find_common_works_between(
        cls, *people: Person, **kwargs: Any
    ) -> list["CoauthoredWork"]:
        query = DataciteQuery().domain("dois").order_by("relevance")
        for person in people:
            query = query.query(creators__name=format_person_name(person))

        # Limit query to only information used in parse works
        query = query.select("doi", "titles", "creators", "dates")

        # For now, limit to only arXiv preprints
        query = query.query(publisher="arXiv")

        if published_after := kwargs.get("published_after"):
            if isinstance(published_after, str):
                try:
                    published_after = date.fromisoformat(published_after)
                except ValueError:
                    print(
                        "Invalid date format for published_after, skipping filter. "
                        "Please use YYYY-MM-DD."
                    )

            if isinstance(published_after, date):
                now = datetime.now().date()
                query = query.query(
                    created=f"[{published_after.isoformat()} TO {now.isoformat()}]"
                )

        data = cls.request(query)
        items = data.get("data", [])

        return [parsed_work for item in items if (parsed_work := cls.parse_work(item))]

    @classmethod
    @override
    def request(cls, query: "DataciteQuery", **kwargs: Any) -> dict[str, Any]:
        cls._limit_rate()
        response = requests.get(
            f"{cls.api_url}/{query.url}",
            headers={"User-Agent": SCIPOST_USER_AGENT},
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        from ethics.models import CoauthoredWork

        attributes = data.get("attributes", {})

        work = CoauthoredWork(
            server_source=PreprintServer.DATACITE.value,
            identifier=data.get("id"),
            doi=attributes.get("doi"),
            title=attributes.get("titles", [""])[0].get("title", "")[:512],
            metadata=data,
        )
        work.authors = [
            HumanName(
                last=author.get("familyName", ""), first=author.get("givenName", "")
            )
            for author in attributes.get("creators", [])
        ]

        dates = attributes.get("dates", [])
        for date_entry in dates:
            try:
                date = datetime.fromisoformat(date_entry.get("date")).date()
            except ValueError:
                continue

            if date_entry.get("dateType") == "Submitted":
                if work.date_published is None or date < work.date_published:
                    work.date_published = date
            elif date_entry.get("dateType") == "Updated":
                if work.date_updated is None or date > work.date_updated:
                    work.date_updated = date

        return work
