# Module for making external api calls as needed in the submissions cycle
import feedparser
import requests
import re

from django.template import Template, Context
from .behaviors import ArxivCallable

from strings import arxiv_caller_errormessages


class DOICaller:
    def __init__(self, doi_string):
        self.doi_string = doi_string
        self._call_crosslink()
        self._format_data()

    def _call_crosslink(self):
        url = 'http://api.crossref.org/works/%s' % self.doi_string
        self.crossref_data = requests.get(url).json()

    def _collect_data(self):
        # read out json here.



# I'm going to revamp this whole thing...
class BaseCaller(object):
    '''Base mixin for caller (Arxiv, DOI).
    The basic workflow is to initiate the caller, call process() to make the actual call
    followed by is_valid() to validate the response of the call.

    An actual caller should inherit at least the following:
    > Properties:
      - query_base_url
      - caller_regex
    > Methods:
      - process()
    '''
    # State of the caller
    _is_processed = False
    caller_regex = None
    errorcode = None
    errorvariables = {}
    errormessages = {}
    identifier_without_vn_nr = ''
    identifier_with_vn_nr = ''
    metadata = {}
    query_base_url = None
    target_object = None
    version_nr = None

    def __init__(self, target_object, identifier, *args, **kwargs):
        '''Initiate the Caller by assigning which object is used
        the Arxiv identifier to be called.

        After initiating call in specific order:
        - process()
        - is_valid()

        Keyword arguments:
        target_object -- The model calling the Caller (object)
        identifier    -- The identifier used for the call (string)
        '''
        try:
            self._check_valid_caller()
        except NotImplementedError as e:
            print('Caller invalid: %s' % e)
            return

        # Set given arguments
        self.target_object = target_object
        self.identifier = identifier
        self._precheck_if_valid()
        super(BaseCaller, self).__init__(*args, **kwargs)

    def _check_identifier(self):
        '''Split the given identifier in an article identifier and version number.'''
        if not self.caller_regex:
            raise NotImplementedError('No regex is set for this caller')

        if re.match(self.caller_regex, self.identifier):
            self.identifier_without_vn_nr = self.identifier.rpartition('v')[0]
            self.identifier_with_vn_nr = self.identifier
            self.version_nr = int(self.identifier.rpartition('v')[2])
        else:
            self.errorvariables['identifier_with_vn_nr'] = self.identifier
            raise ValueError('bad_identifier')

    def _check_valid_caller(self):
        '''Check if all methods and variables are set appropriately'''
        if not self.query_base_url:
            raise NotImplementedError('No `query_base_url` set')

    def _precheck_duplicate(self):
        '''Check if identifier for object already exists.'''
        if self.target_object.same_version_exists(self.identifier_with_vn_nr):
            raise ValueError('preprint_already_submitted')

    def _precheck_previous_submissions_are_valid(self):
        '''Check if previous submitted versions have the appropriate status.'''
        try:
            self.previous_submissions = self.target_object.different_versions(
                                        self.identifier_without_vn_nr)
        except AttributeError:
            # Commentaries do not have previous version numbers?
            pass

        if self.previous_submissions:
            for submission in [self.previous_submissions[0]]:
                if submission.status == 'revision_requested':
                    self.resubmission = True
                elif submission.status in ['rejected', 'rejected_visible']:
                    raise ValueError('previous_submissions_rejected')
                else:
                    raise ValueError('previous_submission_undergoing_refereeing')

    def _precheck_if_valid(self):
        '''The master method to perform all checks required during initializing Caller.'''
        try:
            self._check_identifier()
            self._precheck_duplicate()
            self._precheck_previous_submissions_are_valid()
            # More tests should be called right here...!
        except ValueError as e:
            self.errorcode = str(e)

        return not self.errorcode

    def _post_process_checks(self):
        '''Perform checks after process, to check received data.

        Return:
        None -- Raise ValueError with error code for an invalid check.
        '''
        pass

    def is_valid(self):
        '''Check if the process() call received valid data.

        If `is_valid()` is overwritten in the actual caller, be
        sure to call this parent method in the last line!

        Return:
        boolean -- True for valid data received. False otherwise.
        '''
        if self.errorcode:
            return False
        if not self._is_processed:
            raise ValueError('`process()` should be called first!')
        return True

    def process(self):
        '''Call to receive data.

        The `process()` should be implemented in the actual
        caller be! Be sure to call this parent method in the last line!
        '''
        try:
            self._post_process_checks()
        except ValueError as e:
            self.errorcode = str(e)

        self._is_processed = True

    def get_error_message(self, errormessages={}):
        '''Return the errormessages for a specific error code, with the possibility to
        overrule the default errormessage dictionary for the specific Caller.
        '''
        try:
            t = Template(errormessages[self.errorcode])
        except KeyError:
            t = Template(self.errormessages[self.errorcode])
        return t.render(Context(self.errorvariables))


# class DOICaller(BaseCaller):
#     """Perform a DOI lookup for a given identifier."""
#     pass


class ArxivCaller(BaseCaller):
    """ Performs an Arxiv article lookup for given identifier """

    # State of the caller
    resubmission = False
    previous_submissions = []
    errormessages = arxiv_caller_errormessages
    errorvariables = {
        'arxiv_journal_ref': '',
        'arxiv_doi': '',
        'identifier_with_vn_nr': ''
    }
    arxiv_journal_ref = ''
    arxiv_doi = ''
    metadata = {}
    query_base_url = 'http://export.arxiv.org/api/query?id_list=%s'
    caller_regex = "^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$"

    def __init__(self, target_object, identifier):
        if not issubclass(target_object, ArxivCallable):
            raise TypeError('Given target_object is not an ArxivCallable object.')
        super(ArxivCaller, self).__init__(target_object, identifier)

    def process(self):
        '''Do the actual call the receive Arxiv information.'''
        if self.errorcode:
            return

        queryurl = (self.query_base_url % self.identifier_with_vn_nr)

        try:
            self._response = requests.get(queryurl, timeout=4.0)
        except requests.ReadTimeout:
            self.errorcode = 'arxiv_timeout'
            return
        except requests.ConnectionError:
            self.errorcode = 'arxiv_timeout'
            return

        self._response_content = feedparser.parse(self._response.content)

        super(ArxivCaller, self).process()

    def _post_process_checks(self):
        # Check if response has at least one entry
        if self._response.status_code == 400 or 'entries' not in self._response_content:
            raise ValueError('arxiv_bad_request')

        # Check if preprint exists
        if not self.preprint_exists():
            raise ValueError('preprint_does_not_exist')

        # Check via journal ref if already published
        self.arxiv_journal_ref = self.published_journal_ref()
        self.errorvariables['arxiv_journal_ref'] = self.arxiv_journal_ref
        if self.arxiv_journal_ref:
            raise ValueError('paper_published_journal_ref')

        # Check via DOI if already published
        self.arxiv_doi = self.published_doi()
        self.errorvariables['arxiv_doi'] = self.arxiv_doi
        if self.arxiv_doi:
            raise ValueError('paper_published_doi')

        self.metadata = self._response_content

    def preprint_exists(self):
        return 'title' in self._response_content['entries'][0]

    def published_journal_ref(self):
        if 'arxiv_journal_ref' in self._response_content['entries'][0]:
            return self._response_content['entries'][0]['arxiv_journal_ref']
        return None

    def published_doi(self):
        if 'arxiv_doi' in self._response_content['entries'][0]:
            return self._response_content['entries'][0]['arxiv_doi']
        return None
