__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ...models import UserTag
from ..serializers import UserTagSerializer


class UserTagCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = UserTag.objects.all()
    serializer_class = UserTagSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        data["user"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UserTagDestroyAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserTagSerializer

    def get_queryset(self):
        return UserTag.objects.filter(user=self.request.user)


class UserTagListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserTagSerializer

    def get_queryset(self):
        return self.request.user.email_tags.all()
