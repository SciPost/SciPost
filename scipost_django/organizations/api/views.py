__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from ..models import Organization
from .serializers import (
    OrganizationSerializer,
    OrganizationNAPSerializer,
    OrganizationBalanceSerializer
)
from .viewsets import OrganizationFilterSet


class OrganizationNAPListAPIView(ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationNAPSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.PaginatedCSVRenderer, )
    search_fields = ['name', 'name_original', 'acronym',]
    filterset_class = OrganizationFilterSet
    default_filtering_fields = [
        'name__icontains',
        'name_original__icontains',
        'acronym__icontains'
    ]


class OrganizationBalanceAPIView(RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationBalanceSerializer
