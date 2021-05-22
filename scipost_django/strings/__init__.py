__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


acknowledge_request_thesis_link = (
    "Thank you for your request for a Thesis Link. Your request"
    " will soon be handled by an editor."
)
acknowledge_vet_thesis_link = "Thesis Link request vetted."
acknowledge_request_commentary = (
    "Your request will soon be handled by an Editor. <br>"
    "Thank you for your request for a Commentary Page."
)
acknowledge_submit_comment = (
    "Thank you for contributing a Comment. It will soon be vetted by an Editor."
)
acknowledge_doi_query = "Crossref query by DOI successful."
acknowledge_arxiv_query = "Arxiv query successful."

doi_query_placeholder = 'ex.: 10.21468/00.000.000000'
doi_query_help_text = (
    'For published papers, you can prefill the form (except for domain, subject area and abstract) using the DOI. '
    "(Give the DOI as 10.[4 to 9 digits]/[string], without prefix, as per the placeholder)."
)
doi_query_invalid = (
    "DOI does not match the expression supplied by CrossRef. Either it is very old or you made a mistake. "
    "If you are sure it is correct, please enter the metadata manually. Sorry for the inconvenience."
)

arxiv_query_placeholder = (
    "new style: YYMM.####(#)v#(#) or "
    "old style: cond-mat/YYMM###v#(#)"
)
arxiv_query_help_text =  (
    "For preprints, you can prefill the form using the arXiv identifier. "
    "Give the identifier without prefix and do not forget the version number, as per the placeholder."
)
arxiv_query_invalid = 'ArXiv identifier is invalid. Did you include a version number?'

# Arxiv response is not valid
arxiv_caller_errormessages = {
    'preprint_does_not_exist':
        'A preprint associated to this identifier does not exist.',
    'paper_published_journal_ref':
        ('This paper has been published as {{ arxiv_journal_ref }}'
         '. Please comment on the published version.'),
    'paper_published_doi':
        ('This paper has been published under DOI {{ arxiv_doi }}'
         '. Please comment on the published version.'),
    # 'arxiv_timeout': 'Arxiv did not respond in time. Please try again later',
    # 'arxiv_bad_request':
    #     ('There was an error with requesting identifier ' +
    #      '{{ identifier_with_vn_nr }}'
    #      ' from Arxiv. Please check the identifier and try again.'),
    'previous_submission_undergoing_refereeing':
        ('There exists a preprint with this arXiv identifier '
         'but an earlier version number, which is still undergoing '
         'peer refereeing.'
         'A resubmission can only be performed after request '
         'from the Editor-in-charge. Please wait until the '
         'closing of the previous refereeing round and '
         'formulation of the Editorial Recommendation '
         'before proceeding with a resubmission.'),
    'preprint_already_submitted':
        'This preprint version has already been submitted to SciPost.',
    'previous_submissions_rejected':
        ('This arXiv preprint has previously undergone refereeing '
         'and has been rejected. Resubmission is only possible '
         'if the manuscript has been substantially reworked into '
         'a new arXiv submission with distinct identifier.')
}

arxiv_caller_errormessages_submissions = {
    'paper_published_journal_ref': ('This paper has been published as {{ arxiv_journal_ref }}'
                                    '. You cannot submit it to SciPost anymore.'),
    'paper_published_doi': ('This paper has been published under DOI {{ arxiv_doi }}'
                            '. You cannot submit it to SciPost anymore.')
}
