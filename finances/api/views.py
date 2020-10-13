__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import BasePermission
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r

from ..models import Subsidy
from .serializers import SubsidySerializer


class CanManageSubsidies(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('scipost:can_manage_subsidies')


class SubsidyListAPIView(ListAPIView):
    pagination_class = None
    permission_classes = [CanManageSubsidies]
    queryset = Subsidy.objects.all()
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (r.CSVRenderer, )
    serializer_class = SubsidySerializer
