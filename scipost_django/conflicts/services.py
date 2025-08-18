__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Module for making external api calls as needed in the submissions cycle
from datetime import datetime
from typing import Any
import feedparser
import logging

from common.utils.text import latinise

from .models import ConflictOfInterest

logger = logging.getLogger("scipost.conflicts.arxiv")


class ArxivCaller:
    """
    ArXiv Caller will help retrieve author data from arXiv API.
    """

    query_base_url = "https://export.arxiv.org/api/query?search_query={query}"

    def __init__(self):
        """
        Init ArXivCaller.
        """
        logger.info("Update COI from arXiv")

    def _search_result_present(self, data):
        if len(data.get("entries", [])) > 0:
            return "title" in data["entries"][0]
        return False

    @staticmethod
    def create_conflict(
        profile, rel_profile, entry: dict[str, Any]
    ) -> tuple[ConflictOfInterest, bool]:
        uploaded_date = entry.get("updated", None)
        if isinstance(uploaded_date, str):
            uploaded_date = datetime.fromisoformat(uploaded_date)

        coi, new = ConflictOfInterest.objects.get_or_create(
            header=entry["title"],
            url=entry["link"].replace("http:", "https:"),
            profile=profile,
            related_profile=rel_profile,
            type="coauthor",
            resource_date=uploaded_date,
        )
        return coi, new

    def compare(self, author_profiles, relating_profiles, submission=None):
        """
        Compare two list of Profiles using the arXiv API.
        """

        count = 0
        for profile in author_profiles:
            for rel_profile in relating_profiles:
                search_query = "au:({profile}+AND+({rel_profile}))".format(
                    profile=latinise(profile.last_name),
                    rel_profile=latinise(rel_profile.last_name),
                )
                queryurl = self.query_base_url.format(query=search_query)
                queryurl += "&sortBy=submittedDate&sortOrder=descending&max_results=5"
                queryurl = queryurl.replace(" ", "+")

                # Call the API
                response_content = feedparser.parse(queryurl)
                logger.info(
                    "GET [{profile}] [request] | {url}".format(
                        profile=profile.last_name, url=queryurl
                    )
                )

                if self._search_result_present(response_content):
                    for entry in response_content["entries"]:
                        coi, new = self.create_conflict(profile, rel_profile, entry)
                        if submission:
                            coi.related_submissions.add(submission)
                        count += 1 if new else 0
                    logger.info(
                        "Found results | {response}.".format(response=response_content)
                    )
        return count
