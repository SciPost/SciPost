__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView

from ..models import Organization
from .serializers import OrganizationSerializer, OrganizationBalanceSerializer


class OrganizationListAPIView(ListAPIView):
    queryset = Organization.objects.all().order_by('name')
    serializer_class = OrganizationSerializer


class OrganizationRetrieveAPIView(RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class OrganizationBalanceAPIView(RetrieveAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationBalanceSerializer
