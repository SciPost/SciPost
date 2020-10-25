__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import (
    CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
)

from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ...models import ComposedMessage
from ..serializers import ComposedMessageSerializer
from ...permissions import CanHandleComposedMessage


class ComposedMessageCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = ComposedMessage.objects.all()
    serializer_class = ComposedMessageSerializer
    lookup_field = 'uuid'

    def create(self, request, *args, **kwargs):
        # Override rest_framework.mixins.CreateModelMixin.create in order
        # to include request.user in data, and attachment_uuids for serializer.create
        data = request.data
        data['author'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Attachment uuids passed as extra args to be popped in serializer.create
        serializer.save(attachment_uuids=request.data['attachment_uuids'])
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ComposedMessageUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated, CanHandleComposedMessage,)
    queryset = ComposedMessage.objects.all()
    serializer_class = ComposedMessageSerializer
    lookup_field = 'uuid'

    def update(self, request, *args, **kwargs):
        # Override rest_framework.mixins.CreateModelMixin.update in order
        # to include request.user in data, and attachment_uuids for serializer.update
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(attachment_uuids=request.data['attachment_uuids'])

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ComposedMessageDestroyAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated, CanHandleComposedMessage,)
    serializer_class = ComposedMessageSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        return ComposedMessage.objects.filter_for_user(self.request.user)


class ComposedMessageListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ComposedMessageSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        queryset = ComposedMessage.objects.filter_for_user(self.request.user)
        if self.request.query_params.get('status', None) == 'draft':
            queryset = queryset.filter(status=ComposedMessage.STATUS_DRAFT)
        return queryset
