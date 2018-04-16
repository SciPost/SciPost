__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from .exceptions import ArxivPDFNotFound


def retrieve_pdf_from_arxiv(arxiv_id):
    """
    Try to download the pdf as bytes object from arXiv for a certain arXiv Identifier.
    Raise ArxivPDFNotFound instead.

    :arxiv_id: Arxiv Identifier with or without (takes latest version instead) version number
    """
    path_to_pdf = 'https://arxiv.org/pdf/{arxiv_id}.pdf'.format(arxiv_id=arxiv_id)
    response = requests.get(path_to_pdf)
    if response.status_code != 200:
        raise ArxivPDFNotFound('No pdf found on arXiv.')
    return response.content
