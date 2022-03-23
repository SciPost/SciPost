__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.permissions import AllowAny

from api.viewsets.base import ExtraFilteredReadOnlyModelViewSet
from api.viewsets.mixins import FilteringOptionsActionMixin

from colleges.models import Fellowship
from colleges.api.filtersets import FellowshipPublicAPIFilterSet
from colleges.api.serializers import FellowshipPublicAPISerializer


class FellowshipPublicAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = Fellowship.objects.all()
    permission_classes = [
        AllowAny,
    ]
    serializer_class = FellowshipPublicAPISerializer
    search_fields = [
        "first_name",
        "last_name",
    ]
    ordering_fields = [
        "last_name",
        "acad_field",
    ]
    filterset_class = FellowshipPublicAPIFilterSet
    default_filtering_fields = [
        "last_name__icontains",
        "profile__affiliations__country__name__icontains",
    ]
