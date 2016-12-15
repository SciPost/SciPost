# Module for making external api calls as needed in the submissions cycle
import feedparser

from .models import *


class ArxivCaller():
    def lookup_article(identifier):
        # Pre-checks
        if same_version_exists(identifier)
            return False, "This preprint version has already been submitted to SciPost."

        # Split the given identifier in an article identifier and version number
        identifier_without_vn_nr = identifier.rpartition('v')[0]
        arxiv_vn_nr = int(identifier.rpartition('v')[2])

        resubmission = False
        if previous_submission_undergoing_refereeing(identifier):
            errormessage = '<p>There exists a preprint with this arXiv identifier '
                            'but an earlier version number, which is still undergoing '
                            'peer refereeing.</p>'
                            '<p>A resubmission can only be performed after request '
                            'from the Editor-in-charge. Please wait until the '
                            'closing of the previous refereeing round and '
                            'formulation of the Editorial Recommendation '
                            'before proceeding with a resubmission.</p>'
            return False, errormessage

        # Arxiv query
        queryurl = ('http://export.arxiv.org/api/query?id_list=%s'
                    % identifier)
        arxiv_response = feedparser.parse(queryurl)

        # Check if response has at least one entry
        if not 'entries' in arxiv_response
            errormessage = 'Bad response from Arxiv.'
            return False, errormessage

        # Check if preprint exists
        if not preprint_exists(arxiv_response)
            errormessage = 'A preprint associated to this identifier does not exist.'
            return False, errormessage

        # Check via journal ref if already published
        arxiv_journal_ref = published_journal_ref
        if arxiv_journal_ref
            errormessage = 'This paper has been published as ' + arxiv_journal_ref +
                            '. You cannot submit it to SciPost anymore.'
            return False, resubmission

        # Check via DOI if already published
        arxiv_doi = published_journal_ref
        if arxiv_doi
            errormessage = 'This paper has been published under DOI ' + arxiv_doi
                            + '. You cannot submit it to SciPost anymore.'
            return False, errormessage

        return arxiv_response, ""


    def same_version_exists(identifier):
        return Submission.objects.filter(arxiv_identifier_w_vn_nr=identifier).exists()

    def previous_submission_undergoing_refereeing(identifier):
        previous_submissions = Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=identifier).order_by('-arxiv_vn_nr')

        if previous_submissions:
            return not previous_submissions[0].status == 'revision_requested'
        else:
            return False

    def preprint_exists(arxiv_response):
        return 'title' in arxiv_response['entries'][0]

    def published_journal_ref(arxiv_response):
        if 'arxiv_journal_ref' in arxiv_response['entries'][0]
            return arxiv_response['entries'][0]['arxiv_journal_ref']
        else:
            return False

    def published_DOI(arxiv_response):
        if 'arxiv_doi' in arxiv_response['entries'][0]
            return arxiv_response['entries'][0]['arxiv_doi']
        else:
            return False
