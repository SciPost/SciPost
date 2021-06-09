__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets

from api.viewsets.mixins import FilteringOptionsActionMixin

from ..models import Submission
from ..serializers import SubmissionSerializer


class SubmissionFilterSet(df_filters.FilterSet):
    class Meta:
        model = Submission
        fields = {
            'title': ['icontains', 'startswith',],
            'author_list': ['icontains',],
            'abstract': ['icontains',],
            'acad_field__name': ['icontains',],
            'specialties__name': ['icontains',],
            'topics__name': ['icontains',],
        }


class SubmissionViewSet(FilteringOptionsActionMixin,
                         viewsets.ReadOnlyModelViewSet):
    queryset = Submission.objects.public_newest()
    serializer_class = SubmissionSerializer
    search_fields = ['title', 'author_list', 'abstract']
    filterset_class = SubmissionFilterSet
    default_filtering_fields = [
        'title__icontains',
        'author_list__icontains',
        'abstract__icontains'
    ]
