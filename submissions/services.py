# Module for making external api calls as needed in the submissions cycle
import feedparser
import requests
import pprint
import re
from io import BytesIO

from .models import Submission


class ArxivCaller():
    """ Performs an Arxiv article lookup for given identifier """

    # State of the caller
    isvalid = None
    errorcode = ''
    resubmission = False
    arxiv_journal_ref = ''
    arxiv_doi = ''
    metadata = {}
    query_base_url = 'http://export.arxiv.org/api/query?id_list=%s'
    identifier_without_vn_nr = ''
    identifier_with_vn_nr = ''
    version_nr = None

    def __init__(self):
        pass

    def is_valid(self):
        if self.isvalid is None:
            print("Run process() first")
            return False
        return self.isvalid

    def process(self, identifier):
        # ============================= #
        # Pre-checks                    #
        # ============================= #
        if self.same_version_exists(identifier):
            self.errorcode = 'preprint_already_submitted'
            self.isvalid = False
            return

        # Split the given identifier in an article identifier and version number
        if re.match("^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$", identifier) is None:
            self.errorcode = 'bad_identifier'
            self.isvalid = False
            return

        self.identifier_without_vn_nr = identifier.rpartition('v')[0]
        self.identifier_with_vn_nr = identifier
        self.version_nr = int(identifier.rpartition('v')[2])

        previous_submissions = self.different_versions(self.identifier_without_vn_nr)
        if previous_submissions:
            if previous_submissions[0].status == 'revision_requested':
                resubmission = True
            else:
                self.errorcode = 'previous_submission_undergoing_refereeing'
                self.isvalid = False
                return

        # ============================= #
        # Arxiv query                   #
        # ============================= #
        queryurl = (self.query_base_url % identifier)

        try:
            req = requests.get(queryurl, timeout=4.0)
        except requests.ReadTimeout:
            self.errorcode = 'arxiv_timeout'
            self.isvalid = False
            return
        except requests.ConnectionError:
            self.errorcode = 'arxiv_timeout'
            self.isvalid = False
            return

        content = req.content
        arxiv_response = feedparser.parse(content)

        # Check if response has at least one entry
        if req.status_code == 400 or 'entries' not in arxiv_response:
            self.errorcode = 'arxiv_bad_request'
            self.isvalid = False
            return

        # arxiv_response['entries'][0]['title'] == 'Error'

        # Check if preprint exists
        if not self.preprint_exists(arxiv_response):
            self.errorcode = 'preprint_does_not_exist'
            self.isvalid = False
            return

        # Check via journal ref if already published
        self.arxiv_journal_ref = self.published_journal_ref(arxiv_response)
        if self.arxiv_journal_ref:
            self.errorcode = 'paper_published_journal_ref'
            self.isvalid = False
            return

        # Check via DOI if already published
        self.arxiv_doi = self.published_doi(arxiv_response)
        if self.arxiv_doi:
            self.errorcode = 'paper_published_doi'
            self.isvalid = False
            return

        self.metadata = arxiv_response
        self.isvalid = True
        return

    def same_version_exists(self, identifier):
        return Submission.objects.filter(arxiv_identifier_w_vn_nr=identifier).exists()

    def different_versions(self, identifier):
        return Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=identifier).order_by('-arxiv_vn_nr')

    def check_previous_submissions(self, identifier):
        previous_submissions = Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=identifier).order_by('-arxiv_vn_nr')

        if previous_submissions:
            return not previous_submissions[0].status == 'revision_requested'
        else:
            return False

    def preprint_exists(self, arxiv_response):
        return 'title' in arxiv_response['entries'][0]

    def published_journal_ref(self, arxiv_response):
        if 'arxiv_journal_ref' in arxiv_response['entries'][0]:
            return arxiv_response['entries'][0]['arxiv_journal_ref']
        else:
            return False

    def published_doi(self, arxiv_response):
        if 'arxiv_doi' in arxiv_response['entries'][0]:
            return arxiv_response['entries'][0]['arxiv_doi']
        else:
            return False
