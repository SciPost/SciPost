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
            'title': ['icontains', 'startswith',],
            'author_list': ['icontains',],
            'abstract': ['icontains',],
            'acad_field__name': ['icontains',],
            'specialties__name': ['icontains',],
            'topics__name': ['icontains',],
            'doi_label': ['icontains',],
        }


class PublicationViewSet(FilteringOptionsActionMixin,
                         viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.published().order_by('-publication_date')
    serializer_class = PublicationSerializer
    search_fields = ['title', 'authors_list', 'abstract']
    filterset_class = PublicationFilterSet
    default_filtering_fields = [
        'title__icontains',
        'author_list__icontains',
        'abstract__icontains'
    ]
