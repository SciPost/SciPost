from __future__ import absolute_import, unicode_literals

import logging
import requests

from celery import shared_task, current_task
from mongoengine.python_support import pymongo
from rest_framework import serializers

from django.utils import timezone

from .models import Citable, CitableWithDOI, Journal


logger = logging.getLogger(__name__)


@shared_task
def import_journal_full(issn, cursor='*'):
    """
    Task to query CrossRef for all works of a journal with given ISSN
    and store them in the Metacore mongo database
    """
    return import_journal(issn=issn, cursor=cursor, from_index_date=None)


@shared_task
def import_journal_incremental(issn, from_index_date, cursor='*'):
    """
    Task to query CrossRef for all works of a journal with given ISSN
    from a given date onward and store them in the Metacore mongo database
    """

    # Get from date from the journal itself (necessary for periodic tasks)
    # TODO: make periodic tasks call this function without the date
    journal = Journal.objects.get(ISSN_digital=issn)
    from_index_date = journal.last_full_sync.strftime('%Y-%m-%d')

    import_journal(issn=issn, cursor=cursor, from_index_date=from_index_date)


def import_journal(issn, cursor='*', from_index_date=None):
    # Get journal to track progress

    # Formulate the CR query
    url = 'https://api.crossref.org/journals/{}/works'.format(issn)

    # If the loop is allowed to complete, it fetches (rows * batches) records
    rows = 500
    batches = 2000
    last_cursor = cursor
    total_processed = 0
    error_count = 0
    total_upserted = 0
    total_modified = 0

    validation_errors = []

    for i in range(batches):
        logger.info("-------------------------------")
        logger.info("Batch %s" % (i, ))
        logger.info("Last cursor: {}".format(last_cursor))
        logger.info("Current cursor: {}".format(cursor))

        params = {'cursor': cursor, 'rows': rows, 'mailto': 'jorrandewit@scipost.org'}
        if from_index_date:
            params['filter'] = 'from-index-date:{}'.format(from_index_date)

        last_cursor = cursor
        r = requests.get(url, params=params)
        r_json = r.json()

        citables_json = r_json['message']['items']
        cursor = r_json['message']['next-cursor']
        number_of_results = len(r_json['message']['items'])

        # citables = [parse_crossref_citable(it) for it in citables_json]
        citables = []
        serialized_objects = []
        for cit in citables_json:
            serialized_object = CitableCrossrefSerializer(data=cit)
            if serialized_object.is_valid():
                citables.append(CitableWithDOI(**serialized_object.validated_data))
                serialized_objects.append(serialized_object)
            else:
                # TODO: insert the actual validation errors instead
                citables.append(False)
                logger.info("Error at {}".format(cit))
                validation_errors.append(serialized_object.errors)

        # Parser returns False if there's an error
        errors = [not i for i in citables if i == False]
        error_count = error_count + len(errors)
        citables = [citable for citable in citables if citable]

        # Mass insert in database (will fail on encountering existing documents
        # with same DOI
        if citables:
            operations = [obj.to_UpdateOne() for obj in serialized_objects]
            col = Citable._get_collection()
            bulk_res = col.bulk_write(operations, ordered=False)

            current_task.update_state(state='PROGRESS',
                meta={'current': total_processed, 'errors': error_count, 'last_upserted': bulk_res.upserted_count,
                      'last_matched_count': bulk_res.matched_count, 'last_inserted': bulk_res.inserted_count})

            total_upserted += bulk_res.upserted_count
            total_modified += bulk_res.modified_count
        else:
            current_task.update_state(state='PROGRESS',
                meta={'current': total_processed, 'errors': error_count})

        # Save current count so progress can be tracked in the admin page
        # TODO: make this work (currently only executed after whole import
        # task is completed!
        total_processed += number_of_results
        # Journal.objects.filter(ISSN_digital=issn).update(count_running = total_processed)
        # logger.info('Journal count updated')
        # print('Journal count updated to {}.'.format(Journal.objects.get(ISSN_digital=issn).count_running))

        current_task.send_event('task-started', current=total_processed);

        # For debugging purposes
        logger.info(current_task)
        if citables:
            logger.info("Upserted: {}".format(bulk_res.upserted_count))
            logger.info("Modified: {}".format(bulk_res.modified_count))

        logger.info("Errors: {}".format(error_count))
        logger.info(validation_errors)


        if number_of_results < rows:
            logger.info(number_of_results)
            logger.info('End reached.')
            break

    journal = Journal.objects.get(ISSN_digital=issn)
    journal.count_metacore = Citable.objects(metadata__ISSN=issn).count()
    journal.count_crossref = get_crossref_work_count(issn)

    if journal.count_metacore == journal.count_crossref:
        journal.last_full_sync = timezone.now()

    journal.save()

    # Pack stuff for result
    results = {'total processed': total_processed, 'total inserted': total_upserted, 'total modified': total_modified, 'validation errors': len(validation_errors)}
    return results


def get_crossref_work_count(issn):
    """
    Returns the total number of citables that are present in CR for a given ISSN
    """

    # Formulate the CR query
    url = 'https://api.crossref.org/journals/{}/works'.format(issn)

    # If the loop is allowed to complete, it fetches (rows * batches) records
    rows = 0

    params = {'rows': rows, 'mailto': 'jorrandewit@scipost.org'}
    r = requests.get(url, params=params)
    r_json = r.json()

    result = r_json['message']

    if 'total-results' in result:
        return result['total-results']


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


def add_journal_to_existing(journal_issn=None):
    # Take journal from metadata ('container-title') and put it in top-level 'journal' field
    # for all existing citables
    i = 0
    errors = 0
    if journal_issn:
        print('Using given journal ISSN ', journal_issn)
        cits = Citable.objects(metadata__ISSN=journal_issn, journal__exists=False)
    else:
        cits = Citable.objects(journal__exists=False)

    for cit in cits.only('metadata', 'journal'):
        i = i + 1
        if 'container-title' in cit.metadata:
            journal = cit.metadata['container-title'][0]
            cit.modify(journal=journal)
        else:
            errors = errors + 1

        if i % 1000 == 0:
            print(i)
            print(errors, ' errors')
            print('-------')


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

        except Exception as e:
            logger.error("Error: ", e)
            logger.error(citable_item['DOI'])
            logger.error(citable_item.keys())
            return False


class CitableCrossrefSerializer(serializers.BaseSerializer):
    """
    Class for deserializing a JSON object into the correct form to create a CitableWithDOI out of.
    Specifically for Crossref REST API format

    Usage:
        json_data = { ... }
        serialized_object = CitableCrossrefSerializer(data=json_data)
        serialized_object.is_valid()
        # Validated/parsed data: serialized_object.validated_data
        CitableWithDOI.create(**serialized_object.validated_data)
    """

    def to_internal_value(self, data):
        authors_raw = data.get('author')
        references_raw = data.get('reference')

        doi = data.get('DOI')
        publisher = data.get('publisher')
        # {'issued': {'date-parts': ['...']}}
        publication_date_raw = data.get('issued', {}).get('date-parts', [''])[0]
        # {'title': ['...']}
        title = data.get('title', [''])[0]
        # {'container-title': ['...']}
        journal = data.get('container-title', [''])[0]
        # {'license': [{'url': '...'}]}
        license = data.get('license', [{}])[0].get('URL')
        metadata = data

        # Validation errors
        if not doi:
            raise serializers.ValidationError({'DOI': 'DOI not given.'})
        if not authors_raw:
            raise serializers.ValidationError({'authors': 'Author list is empty.'})
        if not title:
            raise serializers.ValidationError({'title': 'Title is not present.'})
        if not publication_date_raw:
            raise serializers.ValidationError({'publication_date': 'Publication date is missing.'})

        # More complex parsing logic
        publication_date = '-'.join([str(date_part) for date_part in publication_date_raw])

        authors = []
        for author_names in authors_raw:
            author = []
            if 'given' in author_names:
                author.append(author_names['given'])
            if 'family' in author_names:
                author.append(author_names['family'])
            authors.append(' '.join(author))

        if references_raw:
            references_with_doi = [ref for ref in references_raw if 'DOI' in ref]
            references = [ref['DOI'].lower() for ref in references_with_doi]
        else:
            references = []

        return {
            '_cls': CitableWithDOI._class_name,
            'authors': authors,
            'doi': doi.lower(),
            'references': references,
            'publisher': publisher,
            'publication-date': publication_date,
            'title': title,
            'journal': journal,
            'license': license,
            'metadata': metadata
        }

    def to_UpdateOne(self):
        filters = {'doi': self.validated_data.pop('doi')}
        mods = {'$set': self.validated_data}

        return pymongo.UpdateOne(filters, mods, upsert=True)
