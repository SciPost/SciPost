import requests
from .models import Citable, CitableWithDOI
from background_task import background
import logging

logger = logging.getLogger(__name__)

@background()
def import_journal_full(issn, cursor='*'):
    """
    Task to query CrossRef for all works of a journal with given ISSN
    and store them in the Metacore mongo database
    """

    # Formulate the CR query
    url = 'https://api.crossref.org/journals/{}/works'.format(issn)

    # If the loop is allowed to complete, it fetches (rows * batches) records
    rows = 500
    batches = 2000
    last_cursor = cursor

    for i in range(0,batches):
        # print("-------------------------------")
        # print("Batch %s" % (i, ))
        # print("Last cursor: ", last_cursor)
        # print("Current cursor: ", cursor)
        logger.info("-------------------------------")
        logger.info("Batch %s" % (i, ))
        logger.info("Last cursor: ", last_cursor)
        logger.info("Current cursor: ", cursor)

        params = {'cursor': cursor, 'rows': rows, 'mailto': 'b.g.t.ponsioen@uva.nl'}
        last_cursor = cursor
        r = requests.get(url, params=params)
        r_json = r.json()

        citables_json = r_json['message']['items']
        cursor = r_json['message']['next-cursor']
        number_of_results = len(r_json['message']['items'])

        citables = [parse_crossref_citable(it) for it in citables_json]
        # Parser returns False if there's an error
        errors = any([not i for i in citables if i == False])
        orig_citables = citables
        citables = [citable for citable in citables if citable]

        # Mass insert in database (will fail on encountering existing documents
        # with same DOI
        if citables:
            Citable.objects.insert(citables)

        citable = []

        if number_of_results < rows:
            # print(number_of_results)
            # print('End reached.')
            logger.info(number_of_results)
            logger.info('End reached.')
            break

def get_crossref_work_count(issn):
    """
    Returns the total number of citables that are present in CR for a given ISSN
    """

    # Formulate the CR query
    url = 'https://api.crossref.org/journals/{}/works'.format(issn)

    # If the loop is allowed to complete, it fetches (rows * batches) records
    rows = 0

    params = {'rows': rows, 'mailto': 'b.g.t.ponsioen@uva.nl'}
    r = requests.get(url, params=params)
    r_json = r.json()

    result = r_json['message']

    if 'total-results' in result:
        return result['total-results']

def get_crossref_test(cursor='*'):
    """
    For testing purposes - retrieves a "small" dataset from CrossRef and saves it
    in de database, after parsing
    """

    # Member 16 is APS
    # url = 'https://api.crossref.org/members/16/works'
    # Last cursor I used (after 100.000 records from APS) for this
    # cursor = 'AoJ79tDrpd8CPwtodHRwOi8vZHguZG9pLm9yZy8xMC4xMTAzL3BoeXNyZXZiLjQyLjgxMjU='

    # This is PRL
    url = 'https://api.crossref.org/journals/0031-9007/works'
    # cursor = 'AoJ2/dSFrt8CPxFodHRwOi8vZHguZG9pLm9yZy8xMC4xMTAzL3BoeXNyZXZsZXR0LjExMy4yMzY2MDM='

    # If the loop is allowed to complete, it fetches (rows * batches) records
    rows = 500
    batches = 2000
    last_cursor = cursor

    for i in range(0,batches):
        # print("-------------------------------")
        # print("Batch %s" % (i, ))
        # print("Last cursor: ", last_cursor)
        # print("Current cursor: ", cursor)
        logger.info("-------------------------------")
        logger.info("Batch %s" % (i, ))
        logger.info("Last cursor: ", last_cursor)
        logger.info("Current cursor: ", cursor)

        params = {'cursor': cursor, 'rows': rows, 'mailto': 'b.g.t.ponsioen@uva.nl'}
        last_cursor = cursor
        r = requests.get(url, params=params)
        r_json = r.json()

        citables_json = r_json['message']['items']
        cursor = r_json['message']['next-cursor']
        number_of_results = len(r_json['message']['items'])

        citables = [parse_crossref_citable(it) for it in citables_json]
        # Parser returns None if there's an error
        errors = any([not i for i in citables if i == False])
        orig_citables = citables
        citables = [citable for citable in citables if citable]

        # Mass insert in database (will fail on encountering existing documents
        # with same DOI
        if citables:
            Citable.objects.insert(citables)

        citable = []

        if number_of_results < rows:
            # print(number_of_results)
            # print('End reached.')
            logger.info(number_of_results)
            logger.info('End reached.')
            break

def convert_doi_to_lower_case():
    # If you accidentally import 100.000+ records that have random uppercase characters
    # in their reference DOI list
    i = 0
    cits = Citable.objects(__raw__={'references': {'$regex': '([A-Z])\w+'}})
    for cit in cits.only('references'):
        i = i + 1
        refs = [ref.lower() for ref in cit.references]
        cit.modify(references=refs)

        if i % 1000 == 0:
            print(i)


def parse_crossref_citable(citable_item):
    if not citable_item['type'] == 'journal-article':
        return
    
    if 'DOI' in citable_item:
        doi = citable_item['DOI'].lower()
    else:
        return 

    if not Citable.objects(doi=doi):
        try:
            # Parse certain fields for storage on top level in document
            # Blame the convoluted joining and looping on CR

            if 'reference' in citable_item:
                references_with_doi = [ref for ref in citable_item['reference'] if 'DOI' in ref]
                references = [ref['DOI'].lower() for ref in references_with_doi]
            else:
                references = []

            authors = []
            for author_names in citable_item['author']:
                author = []
                if 'given' in author_names:
                    author.append(author_names['given'])
                if 'family' in author_names:
                    author.append(author_names['family'])

                authors.append(' '.join(author))

            publisher = citable_item['publisher']
            title = citable_item['title'][0]
            publication_date = '-'.join([str(date_part) for date_part in citable_item['issued']['date-parts'][0]])
            if 'license' in citable_item:
                license = citable_item['license'][0]['URL']
            else:
                license = ''

            if 'container-title' in citable_item:
                journal = citable_item['container-title'][0]

            return CitableWithDOI(doi=doi, references=references, authors=authors, publisher=publisher, title=title, 
                    publication_date=publication_date, license=license, metadata=citable_item, journal=journal)

            # except BaseException as e:
            #     print("Error!")
            #     print(e)
            #     # raise
        except Exception as e:
            # print("Error: ", e)
            # print(citable_item['DOI'])
            # print(citable_item.keys())
            logger.error("Error: ", e)
            logger.error(citable_item['DOI'])
            logger.error(citable_item.keys())
            return False

