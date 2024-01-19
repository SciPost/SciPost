from django.views import static
import requests
from dataclasses import dataclass, field

from common.utils.text import latinise


@dataclass
class CrossrefResult:
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self._author_list_latinised = [latinise(a).lower() for a in self.author_list]

    @staticmethod
    def _author_str(author: dict):
        if "given" not in author or "family" not in author:
            return ""
        return f"{author['given']} {author['family']}"

    @property
    def title(self):
        return self.metadata.get("title", [""])[0]

    @property
    def author_list(self):
        return [self._author_str(a) for a in self.metadata.get("author", [])]

    @property
    def author_str(self):
        return ", ".join(self.author_list)

    @property
    def doi(self):
        return self.metadata.get("DOI")

    @property
    def doi_url(self):
        return f"https://doi.org/{self.doi}"

    def has_author(self, author):
        if self._author_list_latinised is None:
            return author in self.author_list

        return latinise(author).lower() in self._author_list_latinised

    def __str__(self):
        return f"[{self.doi}] {self.title} by {self.author_str}"

    def __repr__(self):
        return self.__str__()


@dataclass
class CrossrefCIChecker:
    author: str
    authors: list
    possible_works: list = field(default_factory=list)

    @staticmethod
    def fuzzy_match_names(*names):
        """Check that all names are the same, ignoring accents and case"""
        first, *other_names = [latinise(n).lower() for n in names]
        return all([first == name for name in other_names])

    def __post_init__(self):
        if self.authors is None or self.author is None:
            return None

        self.possible_works = self.get_possible_common_works() or []

    def __repr__(self):
        return f"{self.author} vs {self.authors}:\n" + "\n".join(
            [str(w) for w in self.possible_works]
        )

    @staticmethod
    def get_works(queries={}, filters={}, limit=30):
        q = CrossrefQuery()
        for k, v in queries.items():
            q.query(k, v)
        for k, v in filters.items():
            q.filter(k, v)
        q.rows(limit)
        return q.parse()

    def get_possible_common_works(self):
        """
        Returns a list of works that might be common to the author and the authors list.
        """
        query = CrossrefQuery()
        query.metadata["matched_authors"] = [self.author] + self.authors

        crossref_matches = (
            query.query("author", self.author)
            .query("author", self.authors)
            .filter("type", "journal")
            .filter("type", "journal-issue")
            .filter("type", "journal-volume")
            .filter("type", "journal-article")
            .filter("type", "proceedings-series")
            .filter("type", "proceedings-article")
            .filter("type", "book")
            .filter("type", "book-chapter")
            .filter("type", "book-set")
            .filter("type", "book-section")
            .filter("type", "book-track")
            .filter("type", "book-part")
            .filter("type", "book-series")
            .filter("type", "edited-book")
            .parse()
        )

        return crossref_matches

    @property
    def exact_works(self):
        """Returns a list of works whose authors match exactly the person in search of CIs and one of the authors list"""
        if self.possible_works is None:
            return None

        exact_works = []
        for match in self.possible_works:
            has_one_author = any(match.has_author(author) for author in self.authors)
            has_main_author = match.has_author(self.author)

            if has_main_author and has_one_author:
                exact_works.append(match)

        return exact_works


class CrossrefQuery:
    BASE_URL = "https://api.crossref.org/works"

    def __init__(self):
        self._url = self.BASE_URL
        self.metadata = {}

    def query(self, key, value):
        if isinstance(value, list):
            value = "+".join(value)
        self._url += f"|query.{key}={value.replace(' ', '%20')}"
        return self

    def filter(self, key, value):
        if "|filter=" not in self._url:
            self._url += "|filter="
        else:
            self._url += ","
        self._url += f"{key}:{value}"
        return self

    def rows(self, limit):
        self._url += f"rows={limit}"
        return self

    @property
    def url(self):
        """Return the query url after replacing separator placeholders (|) with ? or &,
        such that only the first one is ? and the rest are &"""
        return self._url.replace("|", "?", 1).replace("|", "&")

    def exec(self):
        r = requests.get(self.url)
        if r.status_code == 200:
            return r.json()
        else:
            return None

    def parse(self):
        r = self.exec()
        if r is None:
            return None

        return [
            CrossrefResult(metadata={**metadata, **self.metadata})
            for metadata in r["message"]["items"]
        ]
