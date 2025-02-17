__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Module for making external api calls as needed in the submissions cycle
import re
from typing import Any
from django.db.models import query
import feedparser
import requests
import datetime
import dateutil.parser
import logging

from common.utils import remove_extra_spacing

from submissions.constants import FIGSHARE_PREPRINT_SERVERS
from submissions.models import PreprintServer
from submissions.regexes import CHEMRXIV_DOI_PATTERN

arxiv_logger = logging.getLogger("scipost.services.arxiv")
chemrxiv_logger = logging.getLogger("scipost.services.chemrxiv")
doi_logger = logging.getLogger("scipost.services.doi")
figshare_logger = logging.getLogger("scipost.services.figshare")
osfpreprints_logger = logging.getLogger("scipost.services.osfpreprints")


def extract_publication_date_from_Crossref_data(data):
    date_parts = data.get("issued", {}).get("date-parts", {})
    if date_parts:
        date_parts = date_parts[0]
        year = date_parts[0]
        month = date_parts[1] if len(date_parts) > 1 else 1
        day = date_parts[2] if len(date_parts) > 2 else 1
        pub_date = datetime.date(year, month, day).isoformat()
    else:
        pub_date = ""
    return pub_date


class DOICaller:
    def __init__(self, doi_string):
        self.doi_string = doi_string
        doi_logger.info("New DOI call for %s" % doi_string)

        self._call_crosslink()
        if self.is_valid:
            self._format_data()

    def _call_crosslink(self):
        url = "https://api.crossref.org/works/%s" % self.doi_string
        request = requests.get(url)

        doi_logger.info(
            "GET [{doi}] [request] | {url}".format(
                doi=self.doi_string,
                url=url,
            )
        )

        if request.ok:
            self.is_valid = True
            self._crossref_data = request.json()["message"]
        else:
            self.is_valid = False

        doi_logger.info(
            "GET [{doi}] [response {valid}] | {response}".format(
                doi=self.doi_string,
                valid="VALID" if self.is_valid else "INVALID",
                response=request.text,
            )
        )

    def _format_data(self):
        data = self._crossref_data
        title = data.get("title", [])[0]

        # author_list is given as a comma separated list of names on the relevant models
        author_list = []
        for author in data.get("author", []):
            try:
                author_list.append("{} {}".format(author["given"], author["family"]))
            except KeyError:
                author_list.append(author["name"])
        author_list = ", ".join(author_list)
        abstract = data.get("abstract", "")
        journal = (
            data.get("container-title", [])[0]
            if len(data.get("container-title", [])) > 0
            else ""
        )
        volume = data.get("volume", "")
        pages = self._get_pages(data)
        pub_date = extract_publication_date_from_Crossref_data(data)

        self.data = {
            "title": title,
            "author_list": author_list,
            "abstract": abstract,
            "journal": journal,
            "volume": volume,
            "pages": pages,
            "pub_date": pub_date,
            "crossref_data": self._crossref_data,
        }

        doi_logger.info(
            "GET [{doi}] [formatted data] | {data}".format(
                doi=self.doi_string,
                data=self.data,
            )
        )

    def _get_pages(self, data):
        # For Physical Review
        pages = data.get("article-number", "")
        # For other journals?
        if not pages:
            pages = data.get("page", "")
        return pages


class ArxivCaller:
    """ArXiv Caller will help retrieve Submission data from arXiv API."""

    query_base_url = "https://export.arxiv.org/api/query?id_list=%s"

    def __init__(self, identifier):
        self.identifier = identifier
        arxiv_logger.info("New ArXiv call for identifier %s" % identifier)
        self._call_arxiv()
        if self.is_valid:
            self._format_data()

    def _call_arxiv(self):
        url = self.query_base_url % self.identifier
        request = requests.get(url)
        response_content = feedparser.parse(request.content)
        arxiv_logger.info(
            "GET [{arxiv}] [request] | {url}".format(
                arxiv=self.identifier,
                url=url,
            )
        )

        if self._search_result_present(response_content):
            arxiv_data = response_content["entries"][0]
            self.is_valid = True
            self._arxiv_data = arxiv_data
            self.metadata = response_content
        else:
            self.is_valid = False

        arxiv_logger.info(
            "GET [{arxiv}] [response {valid}] | {response}".format(
                arxiv=self.identifier,
                valid="VALID" if self.is_valid else "INVALID",
                response=response_content,
            )
        )

    def _format_data(self):
        data = self._arxiv_data
        title = remove_extra_spacing(data["title"])
        author_list = [author["name"] for author in data.get("authors", [])]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        arxiv_link = data["id"].replace("http:", "https:")
        abstract = remove_extra_spacing(data["summary"])
        pub_date = dateutil.parser.parse(data["published"]).date()

        self.data = {
            "title": title,
            "author_list": author_list,
            "pub_abstract": abstract,
            "abstract": abstract,  # Duplicate for Commentary/Submission cross-compatibility
            "pub_date": pub_date,
            "arxiv_link": arxiv_link,  # Duplicate for Commentary
            "preprint_server": PreprintServer.objects.get(name="arXiv"),
            "preprint_link": arxiv_link,
        }
        arxiv_logger.info(
            "GET [{arxiv}] [formatted data] | {data}".format(
                arxiv=self.identifier,
                data=self.data,
            )
        )

    def _search_result_present(self, data):
        if len(data.get("entries", [])) > 0:
            return "title" in data["entries"][0]
        return False


class ChemRxivCaller:
    """ChemRxiv Caller will help retrieve Submission data from ChemRxiv API."""

    query_base_url = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items/"
    doi_pattern = r"(https://doi.org/)?" + f"({CHEMRXIV_DOI_PATTERN})"
    url_id_pattern = (
        r"(https://chemrxiv.org/engage/chemrxiv/article-details/)?([a-z0-9]{24})"
    )
    valid_patterns = f"(({doi_pattern})|({url_id_pattern}))"

    def __init__(self, identifier):
        self.identifier = identifier
        chemrxiv_logger.info("New ChemRxiv call for identifier %s" % identifier)

        self.metadata = self._call_chemrxiv()
        self.data = self._format_data(self.metadata) if self.is_valid else None

    def _call_chemrxiv(self):
        if m := re.match(self.doi_pattern, self.identifier):
            doi = m.group(2)
            url = self.query_base_url + "doi/" + doi
        elif m := re.match(self.url_id_pattern, self.identifier):
            item_id = m.group(2)
            url = self.query_base_url + item_id
        else:
            self.is_valid = False
            return

        request = requests.get(url)
        try:
            response_content = request.json()
        except:
            self.is_valid = False
            return

        chemrxiv_logger.info(
            "GET [{chemrxiv}] [request] | {url}".format(
                chemrxiv=self.identifier, url=url
            )
        )

        self.url = url
        self.is_valid = True
        return response_content

    @staticmethod
    def _format_data(data):
        formatted_data = {
            "title": data.get("title", ""),
            "author_list": ", ".join(
                [a["firstName"] + " " + a["lastName"] for a in data.get("authors", [])]
            ),
            "abstract": data.get("abstract", ""),
            "pub_date": dateutil.parser.parse(pub_date)
            if (pub_date := data.get("publishedDate"))
            else None,
            "identifier_w_vn_nr": data.get("doi", ""),
            "preprint_link": "https://doi.org/" + data.get("doi", ""),
        }

        return formatted_data


class FigshareCaller:
    """
    Figshare caller to get data from api.figshare.com.
    """

    query_base_url = "https://api.figshare.com/v2/articles/%s/versions/%s"

    def __init__(self, preprint_server, identifier_w_vn_nr):
        self.preprint_server = preprint_server
        self.identifier_w_vn_nr = identifier_w_vn_nr
        self.identifier = identifier_w_vn_nr.split(".")[0]
        self.version = identifier_w_vn_nr.split(".v")[1]
        figshare_logger.info(
            "New figshare API call for identifier %s.v%s"
            % (self.identifier, self.version)
        )
        self._call_figshare()
        if self.is_valid:
            self._format_data()

    def _call_figshare(self):
        url = self.query_base_url % (self.identifier, self.version)
        request = requests.get(url)
        response_content = request.json()
        figshare_logger.info(
            "GET [{identifier_w_vn_nr} [request] | {url}".format(
                identifier_w_vn_nr=self.identifier_w_vn_nr,
                url=url,
            )
        )
        if self._result_present(response_content):
            self.is_valid = True
            self._figshare_data = response_content
            self.metadata = response_content
        else:
            self.is_valid = False

        figshare_logger.info(
            "GET [{identifier}] [response {valid}] | {response}".format(
                identifier=self.identifier,
                valid="VALID" if self.is_valid else "INVALID",
                response=response_content,
            )
        )

    def _format_data(self):
        """Format data to prefill SubmissionForm as much as possible"""
        title = self._figshare_data["title"]
        author_list = [
            author["full_name"] for author in self._figshare_data.get("authors", [])
        ]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        abstract = self._figshare_data["description"]
        pub_date = self._figshare_data["published_date"]
        figshare_doi = self._figshare_data["doi"]
        identifier_w_vn_nr = (
            self.preprint_server.name.lower() + "_" + self.identifier_w_vn_nr
        )
        self.data = {
            "title": title,
            "author_list": author_list,
            "abstract": abstract,
            "pub_date": pub_date,
            "preprint_server": self.preprint_server,
            "preprint_link": "https://doi.org/" + figshare_doi,
            "identifier_w_vn_nr": identifier_w_vn_nr,
        }

    def _result_present(self, data):
        try:
            return data["id"] == int(self.identifier)
        except KeyError:
            pass
        return False


class OSFPreprintsCaller:
    """
    OSFPreprints caller to get data from api.osf.io.
    """

    query_base_url = (
        "https://api.osf.io/v2/preprints/%s/?embed=contributors&format=json"
    )

    def __init__(self, preprint_server, identifier):
        self.preprint_server = preprint_server
        self.identifier = identifier
        osfpreprints_logger.info(
            "New osfpreprints API call for identifier %s" % self.identifier
        )
        self._call_osfpreprints()
        if self.is_valid:
            self._format_data()

    def _call_osfpreprints(self):
        url = self.query_base_url % self.identifier
        request = requests.get(url)
        response_content = request.json()
        osfpreprints_logger.info(
            "GET [{identifier} [request] | {url}".format(
                identifier=self.identifier,
                url=url,
            )
        )
        if self._result_present(response_content):
            self.is_valid = True
            self._osfpreprints_data = response_content["data"]
            self.metadata = response_content["data"]
        else:
            self.is_valid = False

        osfpreprints_logger.info(
            "GET [{identifier}] [response {valid}] | {response}".format(
                identifier=self.identifier,
                valid="VALID" if self.is_valid else "INVALID",
                response=response_content,
            )
        )

    def _format_data(self):
        """Format data to prefill SubmissionForm as much as possible"""
        title = self._osfpreprints_data["attributes"]["title"]
        contributors_data = self._osfpreprints_data["embeds"]["contributors"]["data"]
        author_list = [
            d["embeds"]["users"]["data"]["attributes"]["full_name"]
            for d in contributors_data
        ]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        abstract = self._osfpreprints_data["attributes"]["description"]
        pub_date = self._osfpreprints_data["attributes"]["date_published"]
        osfpreprints_doi = self._osfpreprints_data["links"]["preprint_doi"]
        identifier_w_vn_nr = self.preprint_server.name.lower() + "_" + self.identifier
        self.data = {
            "title": title,
            "author_list": author_list,
            "abstract": abstract,
            "pub_date": pub_date,
            "preprint_server": self.preprint_server,
            "preprint_link": osfpreprints_doi,
            "identifier_w_vn_nr": identifier_w_vn_nr,
        }

    def _result_present(self, response_content: dict[str, Any]) -> bool:
        data_id = response_content.get("data", {}).get("id", None)
        return data_id == self.identifier
