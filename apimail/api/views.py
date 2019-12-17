__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db.models import Q
from django.utils import timezone

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import filters

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

        return queryset.filter(queryfilter).filter_for_user(request.user)


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
