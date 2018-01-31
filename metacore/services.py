import requests
from .models import Citable, CitableWithDOI

def get_crossref_test():
    """
    For testing purposes - retrieves a small dataset from CrossRef and saves it
    in de database, after parsing
    """
    url = 'https://api.crossref.org/works'
    params = {'query.publisher-name': 'scipost', 'rows': 1000}
    r = requests.get(url, params=params)

    citables_json = r.json()['message']['items']

    citables = [parse_crossref_citable(it) for it in citables_json]
    citables = [citable for citable in citables if citable is not None]

    # Mass insert in database (will fail on encountering existing documents
    # with same DOI
    return Citable.objects.insert(citables)

def parse_crossref_citable(citable_item):
    if not citable_item['type'] == 'journal-article':
        return
    
    if 'DOI' in citable_item:
        doi = citable_item['DOI']
    else:
        return 

    if not Citable.objects(doi=doi):
        try:
            # Parse certain fields for storage on top level in document
            # Blame the convoluted joining and looping on CR
            references_with_doi = [ref for ref in citable_item['reference'] if 'DOI' in ref]
            references = [ref['DOI'] for ref in references_with_doi]
            authors = [' '.join([author_names['given'], author_names['family']]) for author_names in citable_item['author']]
            publisher = citable_item['publisher']
            title = citable_item['title'][0]
            publication_date = '-'.join([str(date_part) for date_part in citable_item['published-online']['date-parts'][0]])
            license = citable_item['license'][0]['URL']

            return CitableWithDOI(doi=doi, references=references, authors=authors, publisher=publisher, title=title, 
                    publication_date=publication_date, license=license, metadata=citable_item)

        except:
            print(citable_item)
            raise
