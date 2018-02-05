from mongoengine import QuerySet


class CitableQuerySet(QuerySet):

    def cited_by(self, dois):
        if isinstance(dois, list):
            return self.only('references').filter(references__in=dois)
        else:
            return self.only('references').filter(references=dois)

    def simple(self):
        return self.only('doi', 'title', 'authors', 'metadata.is-referenced-by-count', 'publication_date', 'publisher')

    def prl(self):
        return self.filter(metadata__ISSN='1079-7114')

    def omni_search(self, query, mode='and'):
        if mode == 'and':
            query_list = query.split(' ')
            query_with_quotes = '"{0}"'.format('" "'.join(query_list))
            return self.search_text(query_with_quotes)
        elif mode == 'or':
            return self.search_text(query)
        else:
            raise ValueError('Invalid mode used in omni_search')

