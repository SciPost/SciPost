from mongoengine import QuerySet


class CitableQuerySet(QuerySet):

    def cited_by(self, dois):
        return self.only('references').filter(references__in=dois)
