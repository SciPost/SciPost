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
    'arxiv_timeout': 'Arxiv did not respond in time. Please try again later',
    'arxiv_bad_request':
        ('There was an error with requesting identifier ' +
         '{{ identifier_with_vn_nr }}'
         ' from Arxiv. Please check the identifier and try again.'),
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
