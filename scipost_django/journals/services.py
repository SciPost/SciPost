__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import logging
import random
import string
import requests
import xml.etree.ElementTree as ET

from django.conf import settings
from django.utils import timezone

from .models import Publication


logger = logging.getLogger(__name__)


def update_citedby(doi_label):
    """
    Run an XML query at Crossref, to update the Cited-by data for a Publication
    """
    publication = Publication.objects.get(doi_label=doi_label)

    # create a doi_batch_id
    salt = ""
    for i in range(5):
        salt = salt + random.choice(string.ascii_letters)
    salt = salt.encode("utf8")
    idsalt = publication.title[:10]
    idsalt = idsalt.encode("utf8")
    doi_batch_id = hashlib.sha1(salt + idsalt).hexdigest()
    query_xml = (
        '<?xml version = "1.0" encoding="UTF-8"?>'
        '<query_batch version="2.0" xmlns = "http://www.crossref.org/qschema/2.0"'
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        'xsi:schemaLocation="http://www.crossref.org/qschema/2.0 '
        'http://www.crossref.org/qschema/crossref_query_input2.0.xsd">'
        "<head>"
        "<email_address>" + settings.CROSSREF_DEPOSIT_EMAIL + "</email_address>"
        "<doi_batch_id>" + str(doi_batch_id) + "</doi_batch_id>"
        "</head>"
        "<body>"
        '<fl_query alert="false">'
        "<doi>" + publication.doi_string + "</doi>"
        "</fl_query>"
        "</body>"
        "</query_batch>"
    )
    url = "http://doi.crossref.org/servlet/getForwardLinks"
    params = {
        "usr": settings.CROSSREF_LOGIN_ID,
        "pwd": settings.CROSSREF_LOGIN_PASSWORD,
        "qdata": query_xml,
        "doi": publication.doi_string,
    }
    r = requests.post(url, params=params)
    if r.status_code == 401:
        print(
            "update_citedby: Crossref credentials are invalid. "
            "Please contact the SciPost Admin."
        )

        logger.info(
            "update_citedby: Crossref credentials are invalid. "
            "Please contact the SciPost Admin."
        )
        return

    try:
        response_deserialized = ET.fromstring(r.text)
    except ET.ParseError:  # something went wrong, abort
        logger.info("Response parsing failed for doi: %s", publication.doi_string)
        return

    prefix = "{http://www.crossref.org/qrschema/2.0}"
    citations = []
    for link in response_deserialized.iter(prefix + "forward_link"):
        citation = {}
        # Cited in Journal, Book, or whatever you want to be cited in.
        link_el = link[0]

        # The only required field in Crossref: doi.
        citation["doi"] = link_el.find(prefix + "doi").text

        if link_el.find(prefix + "article_title") is not None:
            citation["article_title"] = link_el.find(prefix + "article_title").text

        if link_el.find(prefix + "journal_abbreviation") is not None:
            citation["journal_abbreviation"] = link_el.find(
                prefix + "journal_abbreviation"
            ).text

        if link_el.find(prefix + "volume") is not None:
            citation["volume"] = link_el.find(prefix + "volume").text

        if link_el.find(prefix + "first_page") is not None:
            citation["first_page"] = link_el.find(prefix + "first_page").text

        if link_el.find(prefix + "item_number") is not None:
            citation["item_number"] = link_el.find(prefix + "item_number").text

        if link_el.find(prefix + "year") is not None:
            citation["year"] = link_el.find(prefix + "year").text

        if link_el.find(prefix + "issn") is not None:
            citation["issn"] = link_el.find(prefix + "issn").text

        if link_el.find(prefix + "isbn") is not None:
            citation["isbn"] = link_el.find(prefix + "isbn").text

        multiauthors = False
        if link_el.find(prefix + "contributors") is not None:
            for author in link_el.find(prefix + "contributors").iter(
                prefix + "contributor"
            ):
                if author.get("sequence") == "first":
                    if author.find(prefix + "given_name"):
                        citation["first_author_given_name"] = author.find(
                            prefix + "given_name"
                        ).text
                    else:
                        citation["first_author_given_name"] = ""
                    citation["first_author_surname"] = author.find(
                        prefix + "surname"
                    ).text
                else:
                    multiauthors = True
        else:
            citation["first_author_given_name"] = ""
            citation["first_author_surname"] = "[undetermined]"

        citation["multiauthors"] = multiauthors
        citations.append(citation)

    # Update Publication object
    publication.citedby = citations
    publication.number_of_citations = len(citations)
    publication.latest_citedby_update = timezone.now()
    publication.save()
