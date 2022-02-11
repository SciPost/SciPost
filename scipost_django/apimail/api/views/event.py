__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser

from ...models import Event
from ..serializers import EventSerializer


class EventListAPIView(ListAPIView):
    permission_classes = (IsAdminUser,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    lookup_field = "uuid"


class EventRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAdminUser,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    lookup_field = "uuid"
