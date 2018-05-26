__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Module for making external api calls as needed in the submissions cycle
import feedparser
import logging

from scipost.models import Contributor

from .constants import TYPE_COAUTHOR
from .models import ConflictOfInterest, ConflictGroup

logger = logging.getLogger('scipost.conflicts.arxiv')


class ArxivCaller:
    """ArXiv Caller will help retrieve author data from arXiv API."""

    query_base_url = 'https://export.arxiv.org/api/query?search_query={query}'

    def __init__(self, author_list):
        """Init ArXivCaller with list `author_list` as per Submission meta data."""
        self.author_query = ''
        self.conflicts = []

        last_names = []
        for author in author_list:
            # Gather author data to do conflict-of-interest queries with
            last_names.append(author['name'].split()[-1])
        self.author_query = '+OR+'.join(last_names)

        logger.info('Update from ArXiv for author list [{0}]'.format(author_list[:30]))

    def compare_to(self, contributors_list):
        """Add list of Contributors to compare the `author_list` with."""
        for contributor in contributors_list:
            # For each fellow found, so a query with the authors to check for conflicts
            search_query = 'au:({fellow}+AND+({authors}))'.format(
                fellow=contributor.user.last_name, authors=self.author_query)
            queryurl = self.query_base_url.format(query=search_query)
            queryurl += '&sortBy=submittedDate&sortOrder=descending&max_results=5'
            queryurl = queryurl.replace(' ', '+')  # Fallback for some last names with spaces

            # Call the API
            response_content = feedparser.parse(queryurl)
            valid = False
            logger.info('GET [{contributor}] [request] | {url}'.format(
                contributor=contributor.user.last_name, url=queryurl))
            if self._search_result_present(response_content):
                valid = True
                self.conflicts.append({
                    'from': contributor,
                    'results': response_content
                })
            logger.info('{result} | {response}.'.format(
                result='Found results' if valid else 'No results',
                response=response_content))
        return

    def _search_result_present(self, data):
        if len(data.get('entries', [])) > 0:
            return 'title' in data['entries'][0]
        return False

    def add_to_db(self, submission=None):
        """Add found conflicts to database as unverfied co-author conflicts."""
        logger.info('Pushing {} query results to database.'.format(len(self.conflicts)))

        count = 0
        for conflict in self.conflicts:
            # Loop all separate queries
            for result in conflict['results']['entries']:
                coi_group, __ = ConflictGroup.objects.get_or_create(
                    url=result['link'].replace('http:', 'https:'), title=result['title'])
                if submission:
                    coi_group.related_submissions.add(submission)

                # Read all results in one query
                for author in result['authors']:
                    # Try to find an registered Contributor first.
                    contributor = Contributor.objects.active().filter(
                        user__first_name__istartswith=author['name'][0],  # Only use first letter due to database inconsistency
                        user__last_name__iendswith=author['name'].split(' ')[-1]).first()

                    coi, new = ConflictOfInterest.objects.get_or_create(
                        conflict_group=coi_group, origin=conflict['from'],
                        to_contributor=contributor, to_name=author['name'], type=TYPE_COAUTHOR)
                    if new:
                        count += 1
        logger.info('{} new conflicts added.'.format(count))
