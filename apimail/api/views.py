__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.generics import (
    CreateAPIView, DestroyAPIView, ListAPIView,
    RetrieveAPIView, UpdateAPIView)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters, status

from ..models import (
    EmailAccount,
    AttachmentFile,
    ComposedMessage,
    Event,
    StoredMessage, UserTag)

from ..permissions import (
    CanHandleComposedMessage,
    CanHandleStoredMessage, CanReadStoredMessage)

from .serializers import (
    EmailAccountSerializer, EmailAccountAccessSerializer,
    AttachmentFileSerializer,
    ComposedMessageSerializer,
    EventSerializer,
    StoredMessageSerializer,
    UserTagSerializer)


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
        if self.request.query_params.get('current', None) == 'true':
            queryset = queryset.current()
        if self.request.query_params.get('cansend', None) == 'true':
            queryset = queryset.can_send()
        return queryset


class AttachmentFileCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = AttachmentFile.objects.all()
    serializer_class = AttachmentFileSerializer
    parser_classes = [FormParser, MultiPartParser,]


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


class EventListAPIView(ListAPIView):
    permission_classes = (IsAdminUser,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    lookup_field = 'uuid'


class EventRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAdminUser,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    lookup_field = 'uuid'


class StoredMessageFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        queryset = StoredMessage.objects.all()
        queryfilter = Q()

        flow = request.query_params.get('flow', None)
        if flow == 'in':
            # Restrict to incoming emails
            queryset = queryset.exclude(data__sender=request.query_params.get('account'))
        elif flow == 'out':
            # Restrict to outgoing emails
            queryset = queryset.filter(data__sender=request.query_params.get('account'))

        period = request.query_params.get('period', 'any')
        if period != 'any':
            days = 365
            if period == 'month':
                days = 31
            elif period == 'week':
                days = 1
            limit = timezone.now() - datetime.timedelta(days=days)
            queryset = queryset.filter(datetimestamp__gt=limit)

        readstatus = request.query_params.get('read', None)
        if readstatus is not None:
            if readstatus == 'true':
                queryset = queryset.filter(read_by__in=[request.user])
            elif readstatus == 'false':
                queryset = queryset.exclude(read_by__in=[request.user])

        tagpk = request.query_params.get('tag', None)
        if tagpk is not None:
            tag = get_object_or_404(UserTag, pk=tagpk)
            queryset = queryset.filter(tags__in=[tag])

        _from = request.query_params.get('from', None)
        if _from is not None:
            queryfilter = queryfilter | Q(data__from__icontains=_from)
        subject = request.query_params.get('subject', None)
        if subject is not None:
            queryfilter = queryfilter | Q(data__subject__icontains=subject)
        recipients = request.query_params.get('recipients', None)
        if recipients is not None:
            queryfilter = queryfilter | Q(data__recipients__icontains=recipients)

        # For full-text searches through body-plain / body-html, we use a
        # raw SQL query since Django ORM does not support hyphenated lookups,
        # and since Mailgun uses hyphenated keys in its JSON responses.
        body = request.query_params.get('body', None)
        if body is not None:
            query_raw = (
                "SELECT apimail_storedmessage.id FROM apimail_storedmessage "
                "WHERE UPPER((apimail_storedmessage.data ->> %s)::text) LIKE UPPER(%s) "
                "OR UPPER((apimail_storedmessage.data ->> %s)::text) LIKE UPPER(%s) "
                "ORDER BY apimail_storedmessage.datetimestamp DESC;")
            sm_ids = [sm.id for sm in StoredMessage.objects.raw(
                query_raw, ['body-plain', '%%%s%%' % body, 'body-html', '%%%s%%' % body])]
            queryfilter = queryfilter | Q(pk__in=sm_ids)

        return queryset.filter(queryfilter).filter_for_user(
            request.user, request.query_params.get('account'))


class StoredMessageListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = StoredMessage.objects.all()
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'
    filter_backends = [StoredMessageFilterBackend,]


class StoredMessageRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated, CanReadStoredMessage,)
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'


class StoredMessageUpdateReadAPIView(UpdateAPIView):
    """
    Updates the read field (M2M to user) in StoredMessage.
    """

    permission_classes = (IsAuthenticated, CanReadStoredMessage,)
    queryset = StoredMessage.objects.all()
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.read_by.add(request.user)
        instance.save()
        return Response()


class UserTagCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = UserTag.objects.all()
    serializer_class = UserTagSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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


class StoredMessageUpdateTagAPIView(UpdateAPIView):
    """
    Adds or removes a user tag on a StoredMessage.
    """

    permission_classes = [IsAuthenticated, CanReadStoredMessage]
    queryset = StoredMessage.objects.all()
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        tag = get_object_or_404(UserTag, pk=self.request.data.get('tagpk'))
        action = self.request.data.get('action')
        if action == 'add':
            instance.tags.add(tag)
        elif action == 'remove':
            instance.tags.remove(tag)
        instance.save()
        return Response()
