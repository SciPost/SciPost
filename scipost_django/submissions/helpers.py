__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
import requests
import unicodedata

from .exceptions import ArxivPDFNotFound


def retrieve_pdf_from_arxiv(arxiv_id):
    """Try to download the pdf as bytes object from arXiv for a certain arXiv Identifier.
    Raise ArxivPDFNotFound instead.

    :arxiv_id: Arxiv Identifier with or without (takes latest version instead) version number
    """
    path_to_pdf = "https://arxiv.org/pdf/{arxiv_id}.pdf".format(arxiv_id=arxiv_id)
    response = requests.get(path_to_pdf)
    if response.status_code != 200:
        raise ArxivPDFNotFound("No pdf found on arXiv.")
    return response.content


def check_verified_author(submission, user):
    """Check if user is verified author of Submission."""
    if not hasattr(user, "contributor"):
        return False

    return submission.authors.filter(user=user).exists()


def check_unverified_author(submission, user):
    """
    Check if user may be author of Submission.

    Only return true if author is unverified. Verified authors will return false.
    """
    if not hasattr(user, "contributor"):
        return False

    if submission.authors.filter(user=user).exists():
        # User is verified author.
        return False

    return (
        user.last_name in submission.author_list
        and not submission.authors_false_claims.filter(user=user).exists()
    )


def to_ascii_only(str):
    """
    Convert string to lowercase, ASCII-only characters without punctuation and whitespaces.
    """
    str = re.sub(r"[^\w]", "", str).lower()
    return unicodedata.normalize("NFKD", str).encode("ascii", "ignore")
