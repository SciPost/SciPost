__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework.permissions import IsAdminUser

from ..models import Event, StoredMessage
from .serializers import EventSerializer, StoredMessageSerializer


class EventListAPIView(ListAPIView):
    queryset = Event.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = EventSerializer
    lookup_field = 'uuid'


class EventRetrieveAPIView(RetrieveAPIView):
    queryset = Event.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = EventSerializer
    lookup_field = 'uuid'


class StoredMessageListAPIView(ListAPIView):
    queryset = StoredMessage.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'


class StoredMessageRetrieveAPIView(RetrieveAPIView):
    queryset = StoredMessage.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'
