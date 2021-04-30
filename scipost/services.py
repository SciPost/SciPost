__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Module for making external api calls as needed in the submissions cycle
import feedparser
import requests
import datetime
import dateutil.parser
import logging

arxiv_logger = logging.getLogger('scipost.services.arxiv')
doi_logger = logging.getLogger('scipost.services.doi')
figshare_logger = logging.getLogger('scipost.services.figshare')


class DOICaller:
    def __init__(self, doi_string):
        self.doi_string = doi_string
        doi_logger.info('New DOI call for %s' % doi_string)

        self._call_crosslink()
        if self.is_valid:
            self._format_data()

    def _call_crosslink(self):
        url = 'https://api.crossref.org/works/%s' % self.doi_string
        request = requests.get(url)

        doi_logger.info('GET [{doi}] [request] | {url}'.format(
            doi=self.doi_string,
            url=url,
        ))

        if request.ok:
            self.is_valid = True
            self._crossref_data = request.json()['message']
        else:
            self.is_valid = False

        doi_logger.info('GET [{doi}] [response {valid}] | {response}'.format(
            doi=self.doi_string,
            valid='VALID' if self.is_valid else 'INVALID',
            response=request.text,
        ))

    def _format_data(self):
        data = self._crossref_data
        title = data.get('title', [])[0]

        # author_list is given as a comma separated list of names on the relevant models
        author_list = []
        for author in data.get('author', []):
            try:
                author_list.append('{} {}'.format(author['given'], author['family']))
            except KeyError:
                author_list.append(author['name'])
        author_list = ', '.join(author_list)

        journal = data.get('container-title', [])[0]
        volume = data.get('volume', '')
        pages = self._get_pages(data)
        pub_date = self._get_pub_date(data)

        self.data = {
            'title': title,
            'author_list': author_list,
            'journal': journal,
            'volume': volume,
            'pages': pages,
            'pub_date': pub_date,
        }

        doi_logger.info('GET [{doi}] [formatted data] | {data}'.format(
            doi=self.doi_string,
            data=self.data,
        ))

    def _get_pages(self, data):
        # For Physical Review
        pages = data.get('article-number', '')
        # For other journals?
        if not pages:
            pages = data.get('page', '')
        return pages

    def _get_pub_date(self, data):
        date_parts = data.get('issued', {}).get('date-parts', {})
        if date_parts:
            date_parts = date_parts[0]
            year = date_parts[0]
            month = date_parts[1] if len(date_parts) > 1 else 1
            day = date_parts[2] if len(date_parts) > 2 else 1
            pub_date = datetime.date(year, month, day).isoformat()
        else:
            pub_date = ''

        return pub_date


class ArxivCaller:
    """ArXiv Caller will help retrieve Submission data from arXiv API."""

    query_base_url = 'https://export.arxiv.org/api/query?id_list=%s'

    def __init__(self, identifier):
        self.identifier = identifier
        arxiv_logger.info('New ArXiv call for identifier %s' % identifier)
        self._call_arxiv()
        if self.is_valid:
            self._format_data()

    def _call_arxiv(self):
        url = self.query_base_url % self.identifier
        request = requests.get(url)
        response_content = feedparser.parse(request.content)
        arxiv_logger.info('GET [{arxiv}] [request] | {url}'.format(
            arxiv=self.identifier,
            url=url,
        ))

        if self._search_result_present(response_content):
            arxiv_data = response_content['entries'][0]
            self.is_valid = True
            self._arxiv_data = arxiv_data
            self.metadata = response_content
        else:
            self.is_valid = False

        arxiv_logger.info('GET [{arxiv}] [response {valid}] | {response}'.format(
            arxiv=self.identifier,
            valid='VALID' if self.is_valid else 'INVALID',
            response=response_content,
        ))

    def _format_data(self):
        data = self._arxiv_data
        title = data['title']
        author_list = [author['name'] for author in data.get('authors', [])]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        arxiv_link = data['id'].replace('http:', 'https:')
        abstract = data['summary']
        pub_date = dateutil.parser.parse(data['published']).date()

        self.data = {
            'title': title,
            'author_list': author_list,
            'arxiv_link': arxiv_link,
            'pub_abstract': abstract,
            'abstract': abstract,  # Duplicate for Commentary/Submission cross-compatibility
            'pub_date': pub_date,
        }
        arxiv_logger.info('GET [{arxiv}] [formatted data] | {data}'.format(
            arxiv=self.identifier,
            data=self.data,
        ))

    def _search_result_present(self, data):
        if len(data.get('entries', [])) > 0:
            return 'title' in data['entries'][0]
        return False


class FigshareCaller:
    """
    Figshare caller to get data from api.figshare.com.
    """

    query_base_url = 'https://api.figshare.com/v2/articles/%s/versions/%s'

    def __init__(self, identifier_w_vn_nr):
        self.identifier_w_vn_nr = identifier_w_vn_nr
        self.identifier = identifier_w_vn_nr.split('.')[0]
        self.version = identifier_w_vn_nr.split('.v')[1]
        figshare_logger.info(
            'New figshare API call for identifier %s.v%s' % (self.identifier, self.version))
        self._call_figshare()
        if self.is_valid:
            self._format_data()

    def _call_figshare(self):
        url = self.query_base_url % (self.identifier, self.version)
        request = requests.get(url)
        response_content = request.json()
        figshare_logger.info('GET [{identifier_w_vn_nr} [request] | {url}'.format(
            identifier_w_vn_nr=self.identifier_w_vn_nr,
            url=url,
        ))
        if self._result_present(response_content):
            self.is_valid = True
            self._figshare_data = response_content
            self.metadata = response_content
        else:
            self.is_valid = False

        figshare_logger.info('GET [{identifier}] [response {valid}] | {response}'.format(
            identifier=self.identifier,
            valid='VALID' if self.is_valid else 'INVALID',
            response=response_content,
        ))

    def _format_data(self):
        title = self._figshare_data['title']
        author_list = [author['full_name'] for author in self._figshare_data.get('authors', [])]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        chemrxiv_identifier_w_vn_nr = self._figshare_data['doi'].partition('chemrxiv.')[2]
        abstract = self._figshare_data['description']
        pub_date = self._figshare_data['published_date']
        self.data = {
            'title': title,
            'author_list': author_list,
            'chemrxiv_identifier_w_vn_nr': chemrxiv_identifier_w_vn_nr,
            'pub_abstract': abstract,
            'abstract': abstract,  # Duplicate for Commentary/Submission cross-compatibility
            'pub_date': pub_date,
        }
        figshare_logger.info('GET [{identifier}] [formatted data] | {data}'.format(
            identifier=self.identifier,
            data=self.data,
        ))

    def _result_present(self, data):
        if 'id' in data and data['id'] == int(self.identifier):
            return True
        return False
