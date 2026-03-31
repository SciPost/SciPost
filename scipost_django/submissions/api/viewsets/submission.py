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
    ordering_fields = ["submission_date", "latest_activity"]
    filterset_class = SubmissionPublicAPIFilterSet
    default_filtering_fields = [
        "title__icontains",
        "author_list__icontains",
        "abstract__icontains",
    ]

    def get_queryset(self):
        from django.db.models import Prefetch
        from ...models import Report, SubmissionEvent
        from comments.models import Comment
        from journals.models import Publication

        return (
            super()
            .get_queryset()
            .select_related(
                "preprint",
                "acad_field",
                "submitted_to",
                "is_resubmission_of__preprint",
            )
            .prefetch_related(
                "topics",
                "specialties",
                Prefetch(
                    "publications",
                    queryset=Publication.objects.published(),
                    to_attr="published_publications",
                ),
                Prefetch(
                    "events",
                    queryset=SubmissionEvent.objects.for_all(),
                    to_attr="public_events",
                ),
                Prefetch(
                    "reports",
                    queryset=Report.objects.accepted(),
                    to_attr="accepted_reports",
                ),
                Prefetch(
                    "comments",
                    queryset=Comment.objects.vetted(),
                    to_attr="vetted_comments",
                ),
            )
        )


class SubmissionPublicSearchAPIViewSet(
    FilteringOptionsActionMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = Submission.objects.public_latest().unpublished()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = SubmissionPublicSearchSerializer
    search_fields = ["title", "author_list", "abstract"]
    ordering_fields = ["submission_date", "latest_activity"]
    filterset_class = SubmissionPublicSearchAPIFilterSet
    default_filtering_fields = [
        "title__icontains",
        "author_list__icontains",
        "abstract__icontains",
    ]
