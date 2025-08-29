import re
from typing import Any
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode
import requests

from preprints.servers.server import BasePreprintServer


class OSFQuery:
    def __init__(self) -> None:
        self._domain: str = "search"
        self.url_params = MultiValueDict[str, Any]()

    def domain(self, domain: str):
        self._domain = domain
        return self

    def query(self, text: str):
        self.url_params["q"] = text
        return self

    def filter(self, **kwargs: str):
        FILTER_KEY_SYNTAX = "filter[{field}][{lookup}]"
        for key, value in kwargs.items():
            if match := re.match(r"(\w+?)(?:__(\w+))?$", key):
                field, lookup = match.groups()
                if lookup:
                    key = FILTER_KEY_SYNTAX.format(field=field, lookup=lookup)
                else:
                    key = FILTER_KEY_SYNTAX.format(field=field, lookup="")[:-2]
            self.url_params.appendlist(key, value)
        return self

    def embed(self, *args: str):
        for arg in args:
            self.url_params.appendlist("embed", arg)
        return self

    def fields(self, *args: str):
        for arg in args:
            self.url_params.appendlist("fields", arg)
        return self

    @property
    def url(self):
        url_params_lists_joined = {
            key: ",".join(url_param_values)
            for key, url_param_values in self.url_params.lists()
        }
        encoded_params = urlencode(url_params_lists_joined)
        return f"{self._domain}?{encoded_params}"


class OSFServer(BasePreprintServer):
    name = "OSF"
    api_url = "https://api.osf.io/v2"
    base_url = "https://osf.io"
    query_type = OSFQuery

    @classmethod
    def identifier_to_url(cls, identifier: str) -> str:
        return f"https://doi.org/{identifier}/"

    @classmethod
    def query(cls, query: OSFQuery) -> dict[str, Any]:
        response = requests.get(f"{cls.api_url}/{query.url}")
        if not response.ok:
            return {}
        return response.json()

    # @classmethod
    # def parse_work(cls, data: dict[str, Any]) -> "PreprintWork | None":
    #     attributes = data.get("attributes", {})
    #     return PreprintWork(
    #         server=PreprintServer.OSF,
    #         identifier=data.get("doi", ""),
    #         title=attributes.get("title", ""),
    #         authors=[],
    #         date_published=attributes.get("date_created"),
    #         date_updated=attributes.get("date_modified"),
    #         metadata=data,
    #     )
