__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.generics import (
    CreateAPIView, DestroyAPIView, ListAPIView,
    RetrieveAPIView, UpdateAPIView)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters, status

from ..models import (
    EmailAccount, EmailAccountAccess,
    ComposedMessage,
    Event,
    StoredMessage, UserTag)

from ..permissions import CanHandleStoredMessage
from .serializers import (
    EmailAccountSerializer, EmailAccountAccessSerializer,
    ComposedMessageSerializer,
    EventSerializer,
    StoredMessageSerializer,
    UserTagSerializer)


class EmailAccountListAPIView(ListAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = EmailAccountSerializer


class UserEmailAccountAccessListAPIView(ListAPIView):
    """ListAPIView returning request.user's email account accesses."""
    serializer_class = EmailAccountAccessSerializer

    def get_queryset(self):
        queryset = self.request.user.email_account_accesses.all()
        if self.request.query_params.get('current', None) == 'true':
            queryset = queryset.current()
        if self.request.query_params.get('cansend', None) == 'true':
            queryset = queryset.can_send()
        return queryset


class ComposedMessageCreateAPIView(CreateAPIView):
    queryset = ComposedMessage.objects.all()
    serializer_class = ComposedMessageSerializer
    lookup_field = 'uuid'

    def create(self, request, *args, **kwargs):
        # Override rest_framework.mixins.CreateModelMixin.create
        # in order to include request.user in data and link an
        # active account
        data = request.data
        data['author'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ComposedMessageUpdateAPIView(UpdateAPIView):
    queryset = ComposedMessage.objects.all()
    serializer_class = ComposedMessageSerializer
    lookup_field = 'uuid'


class ComposedMessageDestroyAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
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
    queryset = Event.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = EventSerializer
    lookup_field = 'uuid'


class EventRetrieveAPIView(RetrieveAPIView):
    queryset = Event.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = EventSerializer
    lookup_field = 'uuid'


class StoredMessageFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """
    def filter_queryset(self, request, queryset, view):
        queryset = StoredMessage.objects.all()
        queryfilter = Q()

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
            print('subject query: %s' % subject)
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
    queryset = StoredMessage.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'
    filter_backends = [StoredMessageFilterBackend,]


class StoredMessageRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'
    filter_backends = [StoredMessageFilterBackend,]


class StoredMessageUpdateReadAPIView(UpdateAPIView):
    """Updates the read field (M2M to user) in StoredMessage."""
    queryset = StoredMessage.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = StoredMessageSerializer
    lookup_field = 'uuid'
    filter_backends = [StoredMessageFilterBackend,]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.read_by.add(request.user)
        instance.save()
        return Response()


class UserTagListAPIView(ListAPIView):
    serializer_class = UserTagSerializer

    def get_queryset(self):
        return self.request.user.email_tags.all()


class StoredMessageUpdateTagAPIView(UpdateAPIView):
    """Adds or removes a user tag on a StoredMessage."""
    queryset = StoredMessage.objects.all()
    permission_classes = [IsAuthenticated, CanHandleStoredMessage]
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
