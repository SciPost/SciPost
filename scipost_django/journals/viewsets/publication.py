__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets

from api.viewsets.mixins import FilteringOptionsActionMixin

from ..models import Publication
from ..serializers import PublicationSerializer


class PublicationFilterSet(df_filters.FilterSet):
    class Meta:
        model = Publication
        fields = {
            'in_journal__name': ['icontains', 'startswith'],
            'title': ['icontains', 'istartswith', 'iregex'],
            'author_list': ['icontains', 'iregex'],
            'abstract': ['icontains', 'iregex'],
            'publication_date__year': ['exact', 'gte', 'lte'],
            'doi_label': ['icontains',],
            'acad_field__name': ['icontains',],
            'specialties__name': ['icontains',],
            'topics__name': ['icontains',],
        }


class PublicationViewSet(FilteringOptionsActionMixin,
                         viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.published().order_by('-publication_date')
    serializer_class = PublicationSerializer
    search_fields = ['title', 'author_list', 'abstract', 'doi_label']
    ordering_fields = ['publication_date',]
    filterset_class = PublicationFilterSet
    default_filtering_fields = [
        'title__icontains',
        'author_list__icontains',
        'abstract__icontains',
        'doi_label__icontains'
    ]
