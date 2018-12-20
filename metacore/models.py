__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from mongoengine import (
    connect, DynamicDocument, ListField, StringField, DynamicField, URLField, DateTimeField)

from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

from .managers import CitableQuerySet

# Make the connection to MongoDB - this could be put in settings.py as well
# It uses default settings for the mongo server
connect(
    settings.MONGO_DATABASE['database'], host=settings.MONGO_DATABASE['host'],
    username=settings.MONGO_DATABASE['user'], password=settings.MONGO_DATABASE['password'],
    port=settings.MONGO_DATABASE['port'], authSource='admin')


class Citable(DynamicDocument):
    """
    Citable is a generic object in the metacore database - either a version of records
    (with DOI) or preprint of an published/unpublished document.

    NOTE: extra text index for authors/title is defined through mongo shell!
    This should be in the readme, but I'll temporarily add it here for ease of use:
    For the text index, execute this in the mongo shell:
        use scipost
        db.citable.createIndex({authors: "text", title: "text", journal: "text"})
    """

    # Fields that are extracted from the source metadata in order to normalize
    # some of the data for searching / metrics
    references = ListField(StringField())
    authors = ListField(StringField())
    title = StringField()
    publisher = StringField()
    license = URLField()
    publication_date = DateTimeField()
    journal = StringField()

    # Dump all the raw source metadata here
    metadata = DynamicField()

    # Settings for mongoengine
    meta = {
        'queryset_class': CitableQuerySet, # use the custom queryset
        'indexes': ['doi', 'title', 'publication_date', 'publisher', 'references', 'journal'],
        'allow_inheritance': True
    }

    def times_cited(self):
        return []

    def author_list(self, max_n=None):
        if max_n and max_n < len(self.authors):
            return '; '.join(self.authors[:max_n]) + ' et al.'
        else:
            return '; '.join(self.authors)

    def crossref_ref_count(self):
        return self.metadata['is-referenced-by-count']


class CitableWithDOI(Citable):
    """
    CitableWithDOI is the subclass of Citable meant for documents that have a DOI,
    which enables the times_cited metric.
    """
    doi = StringField(require=True, unique=True)

    def times_cited(self):
        return CitableWithDOI.objects.cited_by(self.doi).count()


class Journal(models.Model):
    """Provides interface for importing citables of a journal into Metacore."""

    name = models.CharField(max_length=250, blank=False)
    ISSN_digital = models.CharField(max_length=9, unique=True,
        validators=[RegexValidator(r'^[0-9]{4}-[0-9]{3}[0-9X]$')])
    # Print ISSN not used right now, but there for future use
    ISSN_print = models.CharField(
        max_length=9, blank=True,
        validators=[RegexValidator(r'^[0-9]{4}-[0-9]{3}[0-9X]$')])
    last_full_sync = models.DateTimeField(blank=True, null=True)
    last_cursor = models.CharField(max_length=250, blank=True)
    last_errors = models.TextField(blank=True)
    count_metacore = models.IntegerField(blank=True, null=True)
    count_crossref = models.IntegerField(blank=True, null=True)
    count_running = models.IntegerField(blank=True, null=True) # Tracks progress during import tasks
    last_update = models.DateTimeField(blank=True, null=True, auto_now=True) # Set during import tasks
    last_task_id = models.CharField(max_length=250, blank=True) # Set after task related to journal is started

    def __str__(self):
        return self.name

    def update_count_metacore(self):
         count = Citable.objects(metadata__ISSN=self.ISSN_digital).count()
         self.count_metacore = count

    def update_count_crossref(self):
        """
        Returns the total number of citables that are present in CR for a given ISSN.

        Needs to be merged with .services but need to work out imports first (circular)
        """

        # Formulate the CR query
        url = 'https://api.crossref.org/journals/{}/works'.format(self.ISSN_digital)

        # If the loop is allowed to complete, it fetches (rows * batches) records
        rows = 0

        params = {'rows': rows, 'mailto': 'b.g.t.ponsioen@uva.nl'}
        r = requests.get(url, params=params)
        r_json = r.json()

        result = r_json['message']

        if 'total-results' in result:
            self.count_metacore = result['total-results']


    def purge_citables(self):
        """
        This will delete all citables with their issn set to this journal's issn!
        """

        Citable.objects(metadata__ISSN=self.ISSN_digital).delete()