import requests
from .models import Citable, CitableWithDOI

def get_crossref_test():
    """
    For testing purposes - retrieves a small dataset from CrossRef and saves it
    in de database, after parsing
    """
    # url = 'https://api.crossref.org/works'
    url = 'https://api.crossref.org/members/16/works'
    cursor = '*'
    cursor = 'AoJ79tDrpd8CPwtodHRwOi8vZHguZG9pLm9yZy8xMC4xMTAzL3BoeXNyZXZiLjQyLjgxMjU='
    rows = 1000

    for i in range(1,100):
        print("Batch %s" % (i, ))
        print("-------------------------------")
        print(cursor)
        # params = {'query.publisher-name': 'American Physical Society', 'cursor': cursor, 'rows': rows}
        params = {'cursor': cursor, 'rows': rows, 'mailto': 'b.g.t.ponsioen@uva.nl'}
        r = requests.get(url, params=params)
        r_json = r.json()

        citables_json = r_json['message']['items']
        cursor = r_json['message']['next-cursor']
        number_of_results = len(r_json['message']['items'])
        print(number_of_results)

        citables = [parse_crossref_citable(it) for it in citables_json]
        citables = [citable for citable in citables if citable is not None]

        # Mass insert in database (will fail on encountering existing documents
        # with same DOI
        if citables:
            Citable.objects.insert(citables)

        if number_of_results < rows:
            print('End reached.')
            break

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

            if 'reference' in citable_item:
                references_with_doi = [ref for ref in citable_item['reference'] if 'DOI' in ref]
                references = [ref['DOI'] for ref in references_with_doi]
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

            return CitableWithDOI(doi=doi, references=references, authors=authors, publisher=publisher, title=title, 
                    publication_date=publication_date, license=license, metadata=citable_item)

        except BaseException as e:
            print(e)
            # raise
        except:
            print(citable_item)
