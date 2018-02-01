from django.db import models
from mongoengine import connect, DynamicDocument, ListField, StringField,\
                        DynamicField, URLField, DateTimeField

from .managers import CitableQuerySet


# Make the connection to MongoDB - this could be put in settings.py as well
# It uses default settings for the mongo server
connect('scipost')

class Citable(DynamicDocument):
    """
    Citable is a generic object in the metacore database - either a version of records
    (with DOI) or preprint of an published/unpublished document.
    """

    # Fields that are extracted from the source metadata in order to normalize
    # some of the data for searching / metrics
    references = ListField(StringField())
    authors = ListField(StringField())
    title = StringField()
    publisher = StringField()
    license = URLField()
    publication_date = DateTimeField()

    # Dump all the raw source metadata here
    metadata = DynamicField()

    # Settings for mongoengine
    meta = {
            'queryset_class': CitableQuerySet, # use the custom queryset
            'indexes': ['doi', 'authors', 'title', 'publication_date', 'publisher'], # define indices on database
            'allow_inheritance': True
            }

    def times_cited(self):
        return []

    def author_list(self):
        return '; '.join(self.authors)

    def crossref_ref_count(self):
        return self.metadata['is-referenced-by-count']


class CitableWithDOI(Citable):
    """
    CitableWithDOI is the subclass of Citable meant for documents that have a DOI,
    which enables the times_cited metric
    """
    doi = StringField(require=True, unique=True)

    def times_cited(self):
        return CitableWithDOI.objects.cited_by([self.doi]).count()

