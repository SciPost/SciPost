__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.viewsets.mixins import FilteringOptionsActionMixin

from submissions.models import Submission
from submissions.api.filtersets import (
    SubmissionPublicAPIFilterSet,
    SubmissionPublicSearchAPIFilterSet,
)
from submissions.api.serializers import (
    SubmissionPublicSerializer,
    SubmissionPublicSearchSerializer,
)


class SubmissionPublicAPIViewSet(
    FilteringOptionsActionMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = Submission.objects.public()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = SubmissionPublicSerializer
    search_fields = ["title", "author_list", "abstract"]
    ordering_fields = [
        "submission_date",
    ]
    filterset_class = SubmissionPublicAPIFilterSet
    default_filtering_fields = [
        "title__icontains",
        "author_list__icontains",
        "abstract__icontains",
    ]


class SubmissionPublicSearchAPIViewSet(
    FilteringOptionsActionMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = Submission.objects.public_latest().unpublished()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = SubmissionPublicSearchSerializer
    search_fields = ["title", "author_list", "abstract"]
    ordering_fields = [
        "submission_date",
    ]
    filterset_class = SubmissionPublicSearchAPIFilterSet
    default_filtering_fields = [
        "title__icontains",
        "author_list__icontains",
        "abstract__icontains",
    ]
