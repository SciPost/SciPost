__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from api.viewsets.mixins import FilteringOptionsActionMixin

from journals.api.serializers import PubFracPublicSerializer
from organizations.models import Organization
from organizations.api.filtersets import OrganizationPublicAPIFilterSet
from organizations.api.serializers import (
    OrganizationPublicSerializer,
    OrganizationNAPSerializer,
    OrganizationBalanceSerializer,
)


class OrganizationPublicAPIViewSet(
    FilteringOptionsActionMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = Organization.objects.all()
    permission_classes = [
        AllowAny,
    ]
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (
        r.PaginatedCSVRenderer,
    )
    serializer_class = OrganizationPublicSerializer
    search_fields = [
        "name",
        "name_original",
        "acronym",
    ]
    filterset_class = OrganizationPublicAPIFilterSet
    default_filtering_fields = [
        "name__icontains",
        "name_original__icontains",
        "acronym__icontains",
    ]

    @action(detail=True)
    def pubfracs(self, request, pk=None):
        pubfracs = self.get_object().pubfracs.all()
        serializer = PubFracPublicSerializer(
            pubfracs, many=True, context={"request": self.request}
        )
        return Response(serializer.data)

    @action(detail=True)
    def balance(self, request, pk=None):
        serializer = OrganizationBalanceSerializer(self.get_object())
        return Response(serializer.data)


class OrganizationNAPViewSet(OrganizationPublicAPIViewSet):
    serializer_class = OrganizationNAPSerializer
    ordering_fields = ["name", "cf_nr_associated_publications"]

    def get_view_name(self):
        return "Organization NAP"
