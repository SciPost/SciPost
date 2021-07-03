__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.viewsets.mixins import FilteringOptionsActionMixin

from journals.models import Publication
from journals.api.filtersets import PublicationPublicFilterSet
from journals.api.serializers import PublicationPublicSerializer


class PublicationPublicAPIViewSet(
        FilteringOptionsActionMixin,
        viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.published()
    permission_classes = [AllowAny,]
    serializer_class = PublicationPublicSerializer
    search_fields = ['title', 'author_list', 'abstract', 'doi_label']
    ordering_fields = ['publication_date',]
    filterset_class = PublicationPublicFilterSet
    default_filtering_fields = [
        'title__icontains',
        'author_list__icontains',
        'abstract__icontains',
        'doi_label__icontains'
    ]
