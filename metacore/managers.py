from mongoengine import QuerySet


class CitableQuerySet(QuerySet):

    def cited_by(self, dois):
        return self.only('references').filter(references__in=dois)

    def simple(self):
        return self.only('doi', 'title', 'authors', 'metadata.is-referenced-by-count', 'publication_date', 'publisher')
