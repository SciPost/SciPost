# Module for making external api calls as needed in the submissions cycle
import feedparser
import requests
import datetime
import dateutil.parser
import logging

arxiv_logger = logging.getLogger('scipost.services.arxiv')
doi_logger = logging.getLogger('scipost.services.doi')


class DOICaller:
    def __init__(self, doi_string):
        self.doi_string = doi_string
        doi_logger.info('New DOI call for %s' % doi_string)

        self._call_crosslink()
        if self.is_valid:
            self._format_data()

    def _call_crosslink(self):
        url = 'http://api.crossref.org/works/%s' % self.doi_string
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
        title = data['title'][0]
        author_list = ['{} {}'.format(author['given'], author['family']) for author in data['author']]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        journal = data['container-title'][0]
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
            month = date_parts[1]
            day = date_parts[2]
            pub_date = datetime.date(year, month, day).isoformat()
        else:
            pub_date = ''

        return pub_date


class ArxivCaller:
    query_base_url = 'http://export.arxiv.org/api/query?id_list=%s'

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
        author_list = [author['name'] for author in data['authors']]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        arxiv_link = data['id']
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
