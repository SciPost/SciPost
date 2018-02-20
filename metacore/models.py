from django.db import models
from django.conf import settings

from mongoengine import connect, DynamicDocument, ListField, StringField,\
                        DynamicField, URLField, DateTimeField

from .managers import CitableQuerySet


# Make the connection to MongoDB - this could be put in settings.py as well
# It uses default settings for the mongo server
connect(settings.MONGO_DATABASE['database'],
        host=settings.MONGO_DATABASE['host'],
        username=settings.MONGO_DATABASE['user'],
        password=settings.MONGO_DATABASE['password'],
        port=settings.MONGO_DATABASE['port'],
        authSource='admin')


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
            'indexes': ['doi', 'title', 'publication_date', 'publisher', 'references'], # define indices on database
            'allow_inheritance': True
            }
    """
    NOTE: extra text index for authors/title is defined through mongo shell!
    This should be in the readme, but I'll temporarily add it here for ease of use:
    For the text index, execute this in the mongo shell:
        use scipost
        db.citable.createIndex({authors: "text", title: "text"})
    """

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
        return CitableWithDOI.objects.cited_by(self.doi).count()
