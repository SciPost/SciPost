__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from ...models import Publication


class PublicationPublicAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = Publication
        fields = {
            'title': ['icontains', 'contains', 'istartswith', 'iregex', 'regex'],
            'author_list': ['icontains', 'contains', 'iregex', 'regex'],
            'abstract': ['icontains', 'contains', 'iregex', 'regex'],
            'publication_date': [
                'year', 'month', 'exact',
                'year__gte', 'year__lte', 'year__range',
                'gte', 'lte', 'range'
            ],
            'doi_label': ['icontains',],
            'acad_field__name': ['icontains',],
            'specialties__name': ['icontains',],
            'topics__name': ['icontains',],
        }
