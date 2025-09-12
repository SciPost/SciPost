import re
import feedparser
from datetime import date, datetime
from nameparser import HumanName

from django.utils.http import urlencode

from .utils import Person, QueryFragment, format_person_name
from .server import BasePreprintServer, PreprintServer

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ethics.models import CoauthoredWork

# fmt: off
ARXIV_GROUPS = ["astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph", "math", "CoRR", "q-bio", "q-fin", "stat", "eess", "econ"]
NEW_ARXIV_PATTERN = r"[0-9]{4}\.[0-9]{4,}(?:v[0-9]+)?"  # Match arXiv ids
OLD_ARXIV_PATTERN = (
    rf"(?:{'|'.join(ARXIV_GROUPS)})"    # Match the arXiv group, e.g. "astro-ph"
    + r"(?:\.\w{2})?"                   # Match the subclass identifier, e.g. "astro-ph.CO" or "math.NT"
    + r"\/\d{7,}"                       # Match YY MM NNN format, e.g. "/9812123"
    + r"(?:v[0-9]+)?"                   # Match the version number, e.g. "v2"
)
ARXIV_PREPRINT_IDENTIFIER = rf"(?:{NEW_ARXIV_PATTERN}|{OLD_ARXIV_PATTERN})"
# fmt: on


class ArxivServer(BasePreprintServer):
    name = "arXiv"
    base_url = "https://arxiv.org"
    api_url = "http://export.arxiv.org/api"

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
    def find_common_works_between(
        cls, *people: Person, **kwargs: dict[str, Any]
    ) -> list["CoauthoredWork"]:
        serialized_authors = ";".join([format_person_name(person) for person in people])
        query = QueryFragment("au:" + serialized_authors)

        if published_after := kwargs.get("published_after"):
            if isinstance(published_after, str):
                try:
                    published_after = datetime.fromisoformat(published_after).date()
                except ValueError:
                    print(
                        "Invalid date format for published_after, skipping filter. "
                        "Please use YYYY-MM-DD."
                    )

            if isinstance(published_after, date):
                today_str = datetime.now().date().strftime("%Y%m%d0000")
                published_after_str = published_after.strftime("%Y%m%d0000")
                query &= QueryFragment(
                    f"submittedDate:[{published_after_str} TO {today_str}]"
                )

        results = cls.search(str(query))
        return [
            parsed_work
            for entry in results.entries
            if (parsed_work := cls.parse_work(entry))
        ]

    @classmethod
    def parse_work(cls, data: dict[str, Any]) -> "CoauthoredWork | None":
        from ethics.models import CoauthoredWork

        identifier_wo_vn_nr = doi = None
        if id_match := re.search(ARXIV_PREPRINT_IDENTIFIER, data.get("link", "")):
            identifier = id_match.group(0)
            identifier_wo_vn_nr = re.sub(r"v[0-9]+$", "", identifier)
            doi = "https://doi.org/10.48550/arXiv." + identifier_wo_vn_nr

        work = CoauthoredWork(
            server_source=PreprintServer.ARXIV.value,
            work_type="preprint",
            identifier=identifier_wo_vn_nr,
            doi=doi,
            title=data.get("title", ""),
            metadata=data,
        )
        work.authors = [HumanName(author.name) for author in data.get("authors", [])]
        work.date_published = datetime.fromisoformat(data.get("published", "")).date()
        work.date_updated = datetime.fromisoformat(data.get("updated", "")).date()

        return work
