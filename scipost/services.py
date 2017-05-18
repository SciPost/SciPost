# Module for making external api calls as needed in the submissions cycle
import feedparser
import requests
import re
import datetime
import dateutil.parser

from django.template import Template, Context
from .behaviors import ArxivCallable

from strings import arxiv_caller_errormessages


class DOICaller:
    def __init__(self, doi_string):
        self.doi_string = doi_string
        self._call_crosslink()
        if self.is_valid:
            self._format_data()

    def _call_crosslink(self):
        url = 'http://api.crossref.org/works/%s' % self.doi_string
        request = requests.get(url)
        if request.ok:
            self.is_valid = True
            self._crossref_data = request.json()['message']
        else:
            self.is_valid = False

    def _format_data(self):
        data = self._crossref_data
        pub_title = data['title'][0]
        author_list = ['{} {}'.format(author['given'], author['family']) for author in data['author']]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        journal = data['container-title'][0]
        volume = data.get('volume', '')
        pages = self._get_pages(data)
        pub_date = self._get_pub_date(data)

        self.data = {
            'pub_title': pub_title,
            'author_list': author_list,
            'journal': journal,
            'volume': volume,
            'pages': pages,
            'pub_date': pub_date,
        }

    def _get_pages(self, data):
        # For Physical Review
        pages = data.get('article-number', '')
        # For other journals?
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
        self._call_arxiv()
        if self.is_valid:
            self._format_data()

    def _call_arxiv(self):
        url = self.query_base_url % self.identifier
        request = requests.get(url)
        arxiv_data = feedparser.parse(request.content)['entries'][0]
        if self._search_result_present(arxiv_data):
            self.is_valid = True
            self._arxiv_data = arxiv_data
        else:
            self.is_valid = False

    def _format_data(self):
        data = self._arxiv_data
        pub_title = data['title']
        author_list = [author['name'] for author in data['authors']]
        # author_list is given as a comma separated list of names on the relevant models (Commentary, Submission)
        author_list = ", ".join(author_list)
        arxiv_link = data['id']
        abstract = data['summary']
        pub_date = dateutil.parser.parse(data['published']).date()

        self.data = {
            'pub_title': pub_title,
            'author_list': author_list,
            'arxiv_link': arxiv_link,
            'pub_abstract': abstract,
            'pub_date': pub_date,
        }

    def _search_result_present(self, data):
        return 'title' in data
