__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.permissions import BasePermission
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from api.viewsets.base import ExtraFilteredReadOnlyModelViewSet
from api.viewsets.mixins import FilteringOptionsActionMixin

from finances.models import Subsidy
from finances.api.filtersets import SubsidyFinAdminAPIFilterSet
from finances.api.serializers import SubsidyFinAdminSerializer


class CanManageSubsidies(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('scipost.can_manage_subsidies')


class SubsidyFinAdminAPIViewSet(
        FilteringOptionsActionMixin,
        ExtraFilteredReadOnlyModelViewSet):
    queryset = Subsidy.objects.all()
    permission_classes = [CanManageSubsidies,]
    serializer_class = SubsidyFinAdminSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer, )
    search_fields = [
        'organization__name', 'organization__acronym',
    ]
    ordering_fields = [
        'organization__name',
        'amount',  # this ViewSet is for FinAdmin, no data leak here
        'date',
        'date_until'
    ]
    filterset_class = SubsidyFinAdminAPIFilterSet
    default_filtering_fields = [
        'organization__name__icontains',
        'organization__acronym__icontains'
    ]
