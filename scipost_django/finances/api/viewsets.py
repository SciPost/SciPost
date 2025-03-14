__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from api.viewsets.base import ExtraFilteredReadOnlyModelViewSet
from api.viewsets.mixins import FilteringOptionsActionMixin

from finances.models import Subsidy, SubsidyPayment
from finances.api.filtersets import (
    SubsidyFinAdminAPIFilterSet,
    SubsidyPaymentAPIFilterSet,
)
from finances.api.serializers import SubsidyFinAdminSerializer, SubsidyPaymentSerializer


class CanManageSubsidies(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("scipost.can_manage_subsidies")


class CanUseSubsidyPaymentAPI(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("scipost.can_use_private_api_subsidy_payments")


class SubsidyFinAdminAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = Subsidy.objects.all()
    permission_classes = [
        CanManageSubsidies,
    ]
    serializer_class = SubsidyFinAdminSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer,)
    search_fields = [
        "organization__name",
        "organization__acronym",
    ]
    ordering_fields = [
        "organization__name",
        "amount",  # this ViewSet is for FinAdmin, no data leak here
        "date",
        "date_until",
    ]
    filterset_class = SubsidyFinAdminAPIFilterSet
    default_filtering_fields = [
        "organization__name__icontains",
        "organization__acronym__icontains",
    ]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("organization")
            .prefetch_related("renewal_of")
        )


class SubsidyPublicAPIViewSet(SubsidyFinAdminAPIViewSet):
    queryset = Subsidy.objects.filter(amount_publicly_shown=True)
    permission_classes = [
        AllowAny,
    ]


class SubsidyPaymentPrivateAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = SubsidyPayment.objects.all()
    permission_classes = [
        CanUseSubsidyPaymentAPI,
    ]
    serializer_class = SubsidyPaymentSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer,)
    search_fields = [
        "subsidy__organization__name",
        "subsidy__organization__acronym",
    ]
    filterset_class = SubsidyPaymentAPIFilterSet
    ordering_fields = [
        "subsidy__organization__name",
        "subsidy__amount",
        "amount",
        "date_scheduled",
        "proof_of_payment__date",
        "invoice__date",
    ]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "subsidy",
                "subsidy__organization",
                "proof_of_payment",
                "invoice",
            )
            .prefetch_related("subsidy__renewal_of")
        )
