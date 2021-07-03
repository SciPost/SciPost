__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django_filters import rest_framework as df_filters

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from api.viewsets.mixins import FilteringOptionsActionMixin

from ..models import Organization
from journals.api.serializers import PubFractionPublicSerializer
from .serializers import (
    OrganizationSerializer,
    OrganizationNAPSerializer,
    OrganizationBalanceSerializer
)


class OrganizationFilterSet(df_filters.FilterSet):
    class Meta:
        model = Organization
        fields = {
            'name': ['icontains',],
            'name_original': ['icontains',],
            'acronym': ['icontains',],
            'country': ['exact',],
            'cf_nr_associated_publications': ['gte', 'lte',]
        }


class OrganizationViewSet(FilteringOptionsActionMixin,
                             viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    permission_classes = [AllowAny,]
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.PaginatedCSVRenderer, )
    serializer_class = OrganizationSerializer
    search_fields = ['name', 'name_original', 'acronym',]
    filterset_class = OrganizationFilterSet
    default_filtering_fields = [
        'name__icontains',
        'name_original__icontains',
        'acronym__icontains'
    ]

    @action(detail=True)
    def pubfractions(self, request, pk=None):
        pubfractions = self.get_object().pubfractions.all()
        serializer = PubFractionPublicSerializer(
            pubfractions,
            many=True,
            context={'request': self.request}
        )
        return Response(serializer.data)

    @action(detail=True)
    def balance(self, request, pk=None):
        serializer = OrganizationBalanceSerializer(self.get_object())
        return Response(serializer.data)


class OrganizationNAPViewSet(OrganizationViewSet):
    serializer_class = OrganizationNAPSerializer
    ordering_fields = ['name', 'cf_nr_associated_publications']

    def get_view_name(self):
        return 'Organization NAP'
