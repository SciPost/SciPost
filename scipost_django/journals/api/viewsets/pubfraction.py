__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.viewsets.mixins import FilteringOptionsActionMixin

from journals.models import OrgPubFraction
from journals.api.serializers import PubFractionPublicSerializer

from journals.api.filtersets import PubFractionPublicFilterSet


class PubFractionPublicAPIViewSet(
        FilteringOptionsActionMixin,
        viewsets.ReadOnlyModelViewSet):
    queryset = OrgPubFraction.objects.all()
    permission_classes = [AllowAny,]
    serializer_class = PubFractionPublicSerializer
    search_fields = [
        'organization__name',
        'publication__publication_date__year'
    ]
    ordering_fields = ['-publication_date',]
    filterset_class = PubFractionPublicFilterSet
    default_filtering_fields = [
        'organization__name__icontains',
        'publication__publication_date__year__exact',
    ]
