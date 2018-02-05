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
        return self.filter(metadata__ISSN='0031-9007')

    def omni_search(self, query, mode='and'):
        if mode == 'and':
            query_list = query.split(' ')

            # Treat words that start with '-' (exclude) differently
            query_list_without_excludes = [q for q in query_list if not q[0] == '-']
            query_with_quotes = '"{0}"'.format('" "'.join(query_list_without_excludes))

            query_list_excludes = [q for q in query_list if q not in query_list_without_excludes]
            query_with_quotes = query_with_quotes + ' ' + ' '.join(query_list_excludes) 

            return self.search_text(query_with_quotes)
        elif mode == 'or':
            return self.search_text(query)
        else:
            raise ValueError('Invalid mode used in omni_search')

