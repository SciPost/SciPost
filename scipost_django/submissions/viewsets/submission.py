__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.viewsets.mixins import FilteringOptionsActionMixin

from ..models import Submission
from ..serializers import SubmissionSerializer


class SubmissionFilterSet(df_filters.FilterSet):
    class Meta:
        model = Submission
        fields = {
            'title': ['icontains', 'contains', 'istartswith', 'iregex', 'regex'],
            'author_list': ['icontains', 'contains', 'iregex', 'regex'],
            'abstract': ['icontains', 'contains', 'iregex', 'regex'],
            'submission_date': [
                'date__year', 'date__month', 'date__exact',
                'date__year__gte', 'date__year__lte', 'date__year__range',
                'date__gte', 'date__lte', 'date__range'
            ],
            'acad_field__name': ['icontains',],
            'specialties__name': ['icontains',],
            'topics__name': ['icontains',],
        }


class SubmissionViewSet(FilteringOptionsActionMixin,
                         viewsets.ReadOnlyModelViewSet):
    queryset = Submission.objects.public_newest()
    permission_classes = [AllowAny,]
    serializer_class = SubmissionSerializer
    search_fields = ['title', 'author_list', 'abstract']
    ordering_fields = ['submission_date',]
    filterset_class = SubmissionFilterSet
    default_filtering_fields = [
        'title__icontains',
        'author_list__icontains',
        'abstract__icontains'
    ]
