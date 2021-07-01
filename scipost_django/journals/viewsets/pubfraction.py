__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.viewsets.mixins import FilteringOptionsActionMixin

from ..models import OrgPubFraction
from ..serializers import PubFractionSerializer


class PubFractionFilterSet(df_filters.FilterSet):
    class Meta:
        model = OrgPubFraction
        fields = {
            'organization__name': ['icontains', 'istartswith', 'exact'],
            'organization__country': ['exact',],
            'publication__publication_date': [
                'year', 'month', 'exact',
                'year__gte', 'year__lte', 'year__range',
                'gte', 'lte', 'range'
            ],
            'fraction': ['gte', 'lte', 'exact']
        }


class PubFractionViewSet(FilteringOptionsActionMixin,
                         viewsets.ReadOnlyModelViewSet):
    queryset = OrgPubFraction.objects.all()
    permission_classes = [AllowAny,]
    serializer_class = PubFractionSerializer
    search_fields = [
        'organization__name',
        'publication__publication_date__year'
    ]
    ordering_fields = ['-publication_date',]
    filterset_class = PubFractionFilterSet
    default_filtering_fields = [
        'organization__name__icontains',
        'publication__publication_date__year__exact',
    ]
