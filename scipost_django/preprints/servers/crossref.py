from datetime import date
import requests
from nameparser import HumanName

from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
from django.conf import settings

from .utils import Person, format_person_name
from .server import BasePreprintServer, BaseQuery, PreprintServer

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork


CROSSREF_USER_AGENT = f"SciPost/#{settings.COMMIT_HASH[:8]} (https://scipost.org)"
CROSSREF_MAILTO_ADDRESS = "admin@scipost.org"


class CrossrefQuery(BaseQuery):
    def __init__(self) -> None:
        self._domain: str = "works"
        self.url_params = MultiValueDict[str, Any]()

    def domain(self, domain: str):
        self._domain = domain
        return self

    def query(self, text: str = "", **kwargs: str):
        """
        Provide the query=value parameter.
        Use kwargs for more specific queries like `author=name` for `?query.author=name`.
        """
        if text:
            self.url_params["query"] = text
        self.url_params.update({"query." + k: v for k, v in kwargs.items()})
        return self

    def filter(self, **kwargs: str):
        for key, value in kwargs.items():
            kebab_key = key.replace("_", "-")
            self.url_params.appendlist("filter", f"{kebab_key}:{value}")
        return self

    def select(self, *fields: str):
        self.url_params.update({"select": ",".join(fields)})
        return self

    def order_by(self, key: str):
        ordering = "desc" if key.startswith("-") else "asc"
        self.url_params.update({"sort": key.lstrip("-"), "order": ordering})
        return self

    def __getitem__(self, s: slice):
        offset = s.start or 0
        self.url_params.update({"offset": offset, "rows": s.stop - offset})
        return self

    @property
    def url(self):
        url_params_lists_joined = {
            key: ",".join(url_param_values)
            for key, url_param_values in self.url_params.lists()
        }
        encoded_params = urlencode(url_params_lists_joined)
        return f"{self._domain}?{encoded_params}"


class CrossrefServer(BasePreprintServer):
    name = "Crossref"
    base_url = "https://www.crossref.org"
    api_url = "https://api.crossref.org"
    query_type = CrossrefQuery

    @classmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return f"https://doi.org/{identifier}"

    @classmethod
    def find_common_works_between(
        cls,
        *people: Person,
        **kwargs: dict[str, Any],
    ) -> list["CoauthoredWork"]:
        query = CrossrefQuery().domain("works").order_by("-score")
        for person in people:
            query = query.query(author=format_person_name(person))

        # Limit query to only information used in parse works
        query = query.select("DOI", "title", "author", "published-online", "deposited")

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
                query = query.filter(from_pub_date=published_after.isoformat())

        data = cls.query(query)

        if data and "message" in data:
            items: list[dict[str, Any]] = data["message"].get("items", [])
        else:
            items = []

        return [parsed_work for item in items if (parsed_work := cls.parse_work(item))]

    @classmethod
    def query(cls, query: "CrossrefQuery") -> dict[str, Any]:
        response = requests.get(
            f"{cls.api_url}/{query.url}&mailto={CROSSREF_MAILTO_ADDRESS}",
            headers={"User-Agent": CROSSREF_USER_AGENT},
        )
        if not response.ok:
            return {}

        return response.json()

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        from ethics.models import CoauthoredWork

        def crossref_parse_date(field: dict[str, Any] | None) -> date | None:
            if not field or "date-parts" not in field:
                return None
            try:
                parts = field["date-parts"][0]
                if len(parts) == 3:
                    return date(parts[0], parts[1], parts[2])
                elif len(parts) == 2:
                    return date(parts[0], parts[1], 1)
                elif len(parts) == 1:
                    return date(parts[0], 1, 1)
            except Exception:
                return None
            return None

        doi = data.get("DOI", "")

        work = CoauthoredWork(
            server_source=PreprintServer.CROSSREF.value,
            identifier=doi,
            doi=doi,
            title=data.get("title", [""])[0],
            metadata=data,
        )
        work.authors = [
            HumanName(last=author.get("family", ""), first=author.get("given", ""))
            for author in data.get("author", [])
        ]
        work.date_published = crossref_parse_date(
            data.get("published-online") or data.get("published-print")
        )
        work.date_updated = crossref_parse_date(data.get("deposited"))

        return work
