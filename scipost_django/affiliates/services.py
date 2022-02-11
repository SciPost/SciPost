__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import logging
import requests

from scipost.services import extract_publication_date_from_Crossref_data

from .models import AffiliatePublication

doi_logger = logging.getLogger("scipost.services.doi")


def get_affiliatejournal_publications_from_Crossref(journal):
    """
    For the given journal, get publication items via the Crossref API.

    Parameters
    ----------
    journal :
        An instance of AffiliateJournal
    """
    rows = 20  # we get results in packs of 20 (Crossref default)
    offset = 0  # we keep querying until we hit known publications
    nr_created = 20
    total_nr_created = 0
    # Check number of available results:
    response = requests.get(
        ("http://api.crossref.org/works/" "?filter=container-title:%s&rows=0")
        % journal.name,
    ).json()
    try:
        total_results = response["message"]["total-results"]
    except KeyError:
        return
    if not (type(total_results) == int and total_results > 0):
        doi_logger.error(
            (
                "Incorrect total_results in "
                "affiliates.get_affiliatejournal_publications_from_Crossref "
                "for journal %s: total_results = %s"
            )
            % (journal.name, str(total_results))
        )
        return

    while nr_created > 0 and total_nr_created < total_results:
        nr_created = 0
        response = requests.get(
            (
                "http://api.crossref.org/works/"
                "?filter=container-title:%s&sort=issued&order=desc"
                "&offset=%d"
            )
            % (journal.name, offset),
        ).json()
        try:
            items = response["message"]["items"]
            for item in items:
                if not AffiliatePublication.objects.filter(doi=item["DOI"]).exists():
                    publication_date = extract_publication_date_from_Crossref_data(item)
                    afp = AffiliatePublication(
                        doi=item["DOI"],
                        _metadata_crossref=item,
                        journal=journal,
                        publication_date=publication_date,
                    )
                    afp.save()
                    nr_created += 1
            total_nr_created += nr_created
            offset += rows
        except KeyError:
            pass
    return total_nr_created
