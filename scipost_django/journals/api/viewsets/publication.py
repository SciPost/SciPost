__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models import Q

from rest_framework.permissions import AllowAny

from api.viewsets.base import ExtraFilteredReadOnlyModelViewSet
from api.viewsets.mixins import FilteringOptionsActionMixin

from journals.models import Publication
from journals.regexes import PUBLICATION_DOI_LABEL_REGEX
from journals.api.filtersets import PublicationPublicAPIFilterSet
from journals.api.serializers import PublicationPublicSerializer


class PublicationPublicAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = Publication.objects.published()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = PublicationPublicSerializer
    lookup_field = "doi_label"
    lookup_value_regex = PUBLICATION_DOI_LABEL_REGEX
    search_fields = ["title", "author_list", "abstract", "doi_label"]
    ordering_fields = [
        "publication_date",
    ]
    filterset_class = PublicationPublicAPIFilterSet
    extra_filters = {
        "journal__name": {
            "fields": [
                "in_journal__name",
                "in_issue__in_journal__name",
                "in_issue__in_volume__in_journal__name",
            ],
            "lookups": ["icontains", "istartswith", "iexact", "exact"],
        }
    }
    default_filtering_fields = [
        "title__icontains",
        "author_list__icontains",
        "abstract__icontains",
        "doi_label__icontains",
    ]
