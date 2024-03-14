__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from api.viewsets.mixins import FilteringOptionsActionMixin

from finances.models import PubFrac
from journals.api.serializers import PubFracPublicSerializer

from journals.api.filtersets import PubFracPublicAPIFilterSet


class PubFracPublicAPIViewSet(
    FilteringOptionsActionMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = PubFrac.objects.all()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = PubFracPublicSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer,)
    search_fields = ["organization__name", "publication__publication_date__year"]
    ordering_fields = [
        "-publication_date",
    ]
    filterset_class = PubFracPublicAPIFilterSet
    default_filtering_fields = [
        "organization__name__icontains",
        "publication__publication_date__year__exact",
    ]
