__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from ...models import EmailAccount

from ..serializers import EmailAccountSerializer, EmailAccountAccessSerializer


class EmailAccountListAPIView(ListAPIView):
    permission_classes = (IsAdminUser,)
    queryset = EmailAccount.objects.all()
    serializer_class = EmailAccountSerializer


class UserEmailAccountAccessListAPIView(ListAPIView):
    """
    ListAPIView returning request.user's email account accesses.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = EmailAccountAccessSerializer

    def get_queryset(self):
        queryset = self.request.user.email_account_accesses.all()
        if self.request.query_params.get("current", None) == "true":
            queryset = queryset.current()
        if self.request.query_params.get("cansend", None) == "true":
            queryset = queryset.can_send()
        return queryset
