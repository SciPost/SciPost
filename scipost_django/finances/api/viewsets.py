__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from api.viewsets.base import ExtraFilteredReadOnlyModelViewSet
from api.viewsets.mixins import FilteringOptionsActionMixin

from finances.models import Subsidy, SubsidyPayment
from finances.api.filtersets import (
    SubsidyAPIFilterSet,
    SubsidyPaymentAPIFilterSet,
)
from finances.api.serializers import (
    SubsidyCollectiveSerializer,
    SubsidySerializer,
    SubsidyPaymentSerializer,
)
from finances.models.subsidy import SubsidyCollective


def at_least_one_permission(*permissions: str):
    """
    Custom permission class to check if the user has at least one of the specified permissions.
    """

    class AtLeastOnePermission(BasePermission):
        def has_permission(self, request, view):
            return any(request.user.has_perm(perm) for perm in permissions)

    return AtLeastOnePermission


class SubsidyPrivateAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = Subsidy.objects.all()
    permission_classes = [
        at_least_one_permission(
            "scipost.can_manage_subsidies",
            "scipost.can_use_private_api_subsidies",
        )
    ]
    serializer_class = SubsidySerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer,)
    search_fields = [
        "organization__name",
        "organization__acronym",
    ]
    ordering_fields = [
        "organization__name",
        "amount",  # this ViewSet is for private access, no data leak here
        "date",
        "date_until",
    ]
    filterset_class = SubsidyAPIFilterSet
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


class SubsidyPublicAPIViewSet(SubsidyPrivateAPIViewSet):
    queryset = Subsidy.objects.filter(amount_publicly_shown=True)
    permission_classes = [
        AllowAny,
    ]


class SubsidyPaymentPrivateAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = SubsidyPayment.objects.all()
    permission_classes = [
        at_least_one_permission(
            "scipost.can_manage_subsidies",
            "scipost.can_use_private_api_subsidy_payments",
        )
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


class SubsidyCollectivePrivateAPIViewSet(
    FilteringOptionsActionMixin, ExtraFilteredReadOnlyModelViewSet
):
    queryset = SubsidyCollective.objects.all()
    permission_classes = [
        at_least_one_permission(
            "scipost.can_manage_subsidies",
            "scipost.can_use_private_api_subsidy_collectives",
        )
    ]
    serializer_class = SubsidyCollectiveSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer,)
    search_fields = [
        "coordinator__name",
        "coordinator__acronym",
        "name",
    ]
    ordering_fields = [
        "coordinator__name",
        "name",
    ]

    def get_queryset(self):
        return super().get_queryset().select_related("coordinator")
